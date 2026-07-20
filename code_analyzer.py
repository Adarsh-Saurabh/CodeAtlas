"""
Universal Code Analyzer v2 — with Tensor Shape Computation.
Extracts layers AND computes exact tensor shapes through the network.
"""
from __future__ import annotations
import ast
import os
import math


LAYER_INFO = {
    "Conv2d": {"category": "conv", "title": "Convolution", "color": "#5b9bd5",
               "math": "out = (in - kernel + 2×padding) / stride + 1",
               "desc": "Slides filters across the image to detect patterns like edges and textures."},
    "Conv1d": {"category": "conv", "title": "1D Convolution", "color": "#5b9bd5",
               "math": "out = (in - kernel + 2×padding) / stride + 1",
               "desc": "Slides filters across 1D sequences to detect temporal patterns."},
    "MaxPool2d": {"category": "pool", "title": "Max Pooling", "color": "#ed7d31",
                  "math": "out = in / kernel_size",
                  "desc": "Shrinks feature maps by keeping only the strongest activation in each window."},
    "AvgPool2d": {"category": "pool", "title": "Avg Pooling", "color": "#ed7d31",
                  "math": "out = in / kernel_size",
                  "desc": "Shrinks feature maps by averaging values in each window."},
    "AdaptiveAvgPool2d": {"category": "pool", "title": "Adaptive Avg Pool", "color": "#ed7d31",
                          "math": "out = target_size",
                          "desc": "Pools to a fixed output size regardless of input size."},
    "Linear": {"category": "dense", "title": "Fully Connected", "color": "#70ad47",
               "math": "y = Wx + b",
               "desc": "Every neuron connects to every neuron in the next layer to make final decisions."},
    "ReLU": {"category": "activation", "title": "ReLU", "color": "#ff6348",
             "math": "f(x) = max(0, x)",
             "desc": "Keeps positive values, zeroes out negatives. Adds non-linearity."},
    "LeakyReLU": {"category": "activation", "title": "Leaky ReLU", "color": "#ff6348",
                  "math": "f(x) = max(αx, x)",
                  "desc": "Like ReLU but allows small gradient for negatives."},
    "Sigmoid": {"category": "activation", "title": "Sigmoid", "color": "#ff6348",
                "math": "σ(x) = 1 / (1 + e⁻ˣ)",
                "desc": "Squashes values to range [0, 1]."},
    "Softmax": {"category": "output", "title": "Softmax", "color": "#c00000",
                "math": "P(i) = eˣⁱ / Σeˣʲ",
                "desc": "Converts raw scores into probabilities summing to 100%."},
    "Dropout": {"category": "regularization", "title": "Dropout", "color": "#a5a5a5",
                "math": "mask ~ Bernoulli(p), y = x × mask / (1-p)",
                "desc": "Randomly turns off neurons during training to prevent overfitting."},
    "BatchNorm2d": {"category": "normalization", "title": "Batch Norm", "color": "#a5a5a5",
                    "math": "x̂ = (x - μ) / √(σ² + ε), y = γx̂ + β",
                    "desc": "Normalizes layer outputs for faster, more stable training."},
    "BatchNorm1d": {"category": "normalization", "title": "Batch Norm 1D", "color": "#a5a5a5",
                    "math": "x̂ = (x - μ) / √(σ² + ε), y = γx̂ + β",
                    "desc": "Normalizes 1D feature vectors across a batch."},
    "Flatten": {"category": "reshape", "title": "Flatten", "color": "#ffc000",
                "math": "reshape(C×H×W → C*H*W)",
                "desc": "Converts 3D feature maps into a 1D vector for dense layers."},
    "LSTM": {"category": "recurrent", "title": "LSTM", "color": "#5b9bd5",
             "math": "hₜ = oₜ ⊙ tanh(cₜ)",
             "desc": "Processes sequences step-by-step, remembering long-range info."},
    "GRU": {"category": "recurrent", "title": "GRU", "color": "#5b9bd5",
            "math": "hₜ = (1-zₜ)⊙hₜ₋₁ + zₜ⊙h̃ₜ",
            "desc": "Simplified recurrent unit — faster than LSTM."},
    "Embedding": {"category": "embedding", "title": "Embedding", "color": "#5b9bd5",
                  "math": "lookup(token_id) → vector",
                  "desc": "Converts discrete tokens into dense vectors."},
}


def compute_shapes(layers, input_shape):
    """
    Given a list of layer dicts and an input shape (C, H, W) or (features,),
    compute the output shape after each layer.
    """
    shape = list(input_shape)  # mutable copy
    results = []

    for layer in layers:
        ltype = layer["type"]
        params = layer.get("params", {})
        in_shape = tuple(shape)

        if ltype in ("Conv2d", "Conv1d"):
            out_ch = params.get("out_channels", shape[0])
            kernel = params.get("kernel_size", 3)
            padding = params.get("padding", 0)
            stride = params.get("stride", 1)
            if len(shape) == 3:
                new_h = math.floor((shape[1] - kernel + 2 * padding) / stride + 1)
                new_w = math.floor((shape[2] - kernel + 2 * padding) / stride + 1)
                shape = [out_ch, new_h, new_w]
            else:
                shape = [out_ch] + shape[1:]

        elif ltype in ("MaxPool2d", "AvgPool2d"):
            kernel = params.get("kernel_size", 2)
            stride = params.get("stride", kernel)
            if len(shape) == 3:
                shape = [shape[0], math.floor(shape[1] / stride), math.floor(shape[2] / stride)]

        elif ltype == "AdaptiveAvgPool2d":
            target = params.get("output_size", (1, 1))
            if isinstance(target, int):
                target = (target, target)
            if len(shape) == 3:
                shape = [shape[0], target[0], target[1]]

        elif ltype == "Flatten":
            total = 1
            for d in shape:
                total *= d
            shape = [total]

        elif ltype in ("Linear", "Dense"):
            out_f = params.get("out_features", shape[-1])
            shape = [out_f]

        # Activations, Dropout, BatchNorm don't change shape
        # ReLU, Sigmoid, Softmax, Dropout, BatchNorm2d, BatchNorm1d

        results.append({
            **layer,
            "input_shape": in_shape,
            "output_shape": tuple(shape),
        })

    return results


class UniversalAnalyzer:
    def __init__(self):
        self.layers = []

    def analyze(self, root_dir):
        all_code = {}
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if fname.endswith(".py"):
                    fpath = os.path.join(dirpath, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            all_code[fname] = f.read()
                    except Exception:
                        pass

        if not all_code:
            return self._empty()

        # Detect type
        all_text = "\n".join(all_code.values())
        nn_score = sum(1 for p in ["nn.Module", "nn.Conv", "nn.Linear", "torch", "forward(self"]
                       if p in all_text)
        web_score = sum(1 for p in ["@app.route", "@app.get", "Flask(", "FastAPI(", "from flask", "from fastapi"]
                        if p in all_text)

        if nn_score >= 2:
            return self._analyze_nn(all_code)
        elif web_score >= 2:
            return self._analyze_web(all_code)
        else:
            return self._analyze_generic(all_code)

    def _analyze_nn(self, code_files):
        raw_layers = []
        input_shape = (3, 32, 32)  # default CIFAR-like

        for fname, code in code_files.items():
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    is_nn = any(
                        (isinstance(b, ast.Attribute) and b.attr == "Module") or
                        (isinstance(b, ast.Name) and b.id in ("Module",))
                        for b in node.bases
                    )
                    if is_nn:
                        extracted = self._extract_from_class(node)
                        if extracted:
                            raw_layers = extracted
                            # Try to infer input shape from first Conv
                            for l in raw_layers:
                                if l["type"] in ("Conv2d",) and "in_channels" in l.get("params", {}):
                                    in_ch = l["params"]["in_channels"]
                                    if in_ch == 1:
                                        input_shape = (1, 28, 28)  # MNIST-like
                                    elif in_ch == 3:
                                        input_shape = (3, 32, 32)  # CIFAR-like
                                    break

        if not raw_layers:
            # Fallback: scan any calls
            for fname, code in code_files.items():
                try:
                    tree = ast.parse(code)
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        name = self._call_name(node)
                        if name and name in LAYER_INFO:
                            raw_layers.append({"type": name, "params": self._parse_params(node)})

        if not raw_layers:
            return self._analyze_generic(code_files)

        # Compute shapes
        shaped_layers = compute_shapes(raw_layers, input_shape)

        # Build output
        nodes = []
        # Input node
        nodes.append({
            "id": "input",
            "type": "Input",
            "category": "input",
            "title": "INPUT",
            "shape": list(input_shape),
            "shape_label": f"({' × '.join(str(d) for d in input_shape)})",
            "color": "#4472c4",
            "description": "Raw input data fed into the network.",
            "math": "",
        })

        for i, layer in enumerate(shaped_layers):
            info = LAYER_INFO.get(layer["type"], {})
            out_shape = layer["output_shape"]
            in_shape = layer["input_shape"]
            nodes.append({
                "id": f"layer_{i}",
                "type": layer["type"],
                "category": info.get("category", "other"),
                "title": info.get("title", layer["type"]),
                "shape": list(out_shape),
                "shape_label": f"({' × '.join(str(d) for d in out_shape)})",
                "input_shape_label": f"({' × '.join(str(d) for d in in_shape)})",
                "color": info.get("color", "#747d8c"),
                "description": info.get("desc", ""),
                "math": info.get("math", ""),
                "params": layer.get("params", {}),
                "params_label": self._format_params(layer.get("params", {})),
            })

        # Output node
        final_shape = shaped_layers[-1]["output_shape"] if shaped_layers else input_shape
        nodes.append({
            "id": "output",
            "type": "Output",
            "category": "output",
            "title": "OUTPUT",
            "shape": list(final_shape),
            "shape_label": f"({' × '.join(str(d) for d in final_shape)})",
            "color": "#c00000",
            "description": "Final prediction output.",
            "math": "",
        })

        return {"nodes": nodes, "meta": {"type": "neural_network", "input_shape": list(input_shape)}}

    def _extract_from_class(self, class_node):
        init_layers = {}  # attr_name -> {type, params}
        forward_order = []

        for item in class_node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            if item.name == "__init__":
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Assign):
                        for t in stmt.targets:
                            if (isinstance(t, ast.Attribute) and
                                isinstance(t.value, ast.Name) and t.value.id == "self" and
                                isinstance(stmt.value, ast.Call)):
                                name = self._call_name(stmt.value)
                                if name and name in LAYER_INFO:
                                    init_layers[t.attr] = {
                                        "type": name,
                                        "params": self._parse_params(stmt.value)
                                    }
            elif item.name == "forward":
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Call):
                        cname = self._call_name(stmt)
                        if cname and cname in init_layers:
                            if cname not in [f for f in forward_order]:
                                forward_order.append(cname)

        if forward_order:
            return [init_layers[n] for n in forward_order if n in init_layers]
        return list(init_layers.values())

    def _call_name(self, node):
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
                return node.func.attr
            return node.func.attr
        elif isinstance(node.func, ast.Name):
            return node.func.id
        return None

    def _parse_params(self, call_node):
        params = {}
        args = call_node.args
        kw = {k.arg: k.value for k in call_node.keywords}

        func_name = self._call_name(call_node)

        if func_name in ("Conv2d", "Conv1d", "Conv3d"):
            if len(args) >= 1 and isinstance(args[0], ast.Constant):
                params["in_channels"] = args[0].value
            if len(args) >= 2 and isinstance(args[1], ast.Constant):
                params["out_channels"] = args[1].value
            if len(args) >= 3:
                params["kernel_size"] = self._const_val(args[2], 3)
            if "kernel_size" in kw:
                params["kernel_size"] = self._const_val(kw["kernel_size"], 3)
            if "padding" in kw:
                params["padding"] = self._const_val(kw["padding"], 0)
            if "stride" in kw:
                params["stride"] = self._const_val(kw["stride"], 1)
            params.setdefault("kernel_size", 3)
            params.setdefault("padding", 0)
            params.setdefault("stride", 1)

        elif func_name in ("MaxPool2d", "AvgPool2d"):
            if len(args) >= 1:
                params["kernel_size"] = self._const_val(args[0], 2)
            if "kernel_size" in kw:
                params["kernel_size"] = self._const_val(kw["kernel_size"], 2)
            params.setdefault("kernel_size", 2)

        elif func_name == "AdaptiveAvgPool2d":
            if len(args) >= 1:
                val = args[0]
                if isinstance(val, ast.Tuple) and len(val.elts) == 2:
                    params["output_size"] = (self._const_val(val.elts[0], 1), self._const_val(val.elts[1], 1))
                elif isinstance(val, ast.Constant):
                    params["output_size"] = (val.value, val.value)
            params.setdefault("output_size", (1, 1))

        elif func_name in ("Linear", "Dense"):
            if len(args) >= 1:
                params["in_features"] = self._const_val(args[0], 0)
            if len(args) >= 2:
                params["out_features"] = self._const_val(args[1], 0)

        elif func_name == "Dropout":
            if len(args) >= 1 and isinstance(args[0], ast.Constant):
                params["p"] = args[0].value
            if "p" in kw and isinstance(kw["p"], ast.Constant):
                params["p"] = kw["p"].value

        elif func_name in ("BatchNorm2d", "BatchNorm1d"):
            if len(args) >= 1 and isinstance(args[0], ast.Constant):
                params["num_features"] = args[0].value

        return params

    def _const_val(self, node, default):
        if isinstance(node, ast.Constant):
            return node.value
        return default

    def _format_params(self, params):
        if not params:
            return ""
        parts = [f"{k}={v}" for k, v in params.items()]
        return ", ".join(parts)

    def _analyze_web(self, code_files):
        nodes = []
        all_text = "\n".join(code_files.values())

        # Client
        nodes.append({
            "id": "client", "type": "Client", "category": "client",
            "title": "CLIENT", "shape": [], "shape_label": "Browser / App",
            "color": "#4472c4", "math": "",
            "description": "The user's browser or mobile app sends HTTP requests to the server."
        })

        # Middleware detection
        has_cors = "cors" in all_text.lower() or "CORSMiddleware" in all_text
        has_auth = "auth" in all_text.lower() or "token" in all_text.lower() or "jwt" in all_text.lower()
        if has_cors or has_auth:
            label = "Auth + CORS" if (has_cors and has_auth) else ("CORS" if has_cors else "Auth")
            nodes.append({
                "id": "middleware", "type": "Middleware", "category": "cache",
                "title": f"MIDDLEWARE", "shape": [], "shape_label": label,
                "color": "#a5a5a5", "math": "",
                "description": "Intercepts requests before they reach handlers. Handles authentication, CORS, logging, rate limiting."
            })

        # Server
        framework = "FastAPI" if "FastAPI" in all_text else ("Flask" if "Flask" in all_text else "Server")
        nodes.append({
            "id": "server", "type": "Server", "category": "server",
            "title": f"{framework.upper()} SERVER", "shape": [], "shape_label": framework,
            "color": "#70ad47", "math": "",
            "description": f"The {framework} application server receives requests, routes them to handlers, and sends responses."
        })

        # Routes
        routes_found = []
        for fname, code in code_files.items():
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for dec in node.decorator_list:
                        dec_str = ast.dump(dec)
                        if any(kw in dec_str for kw in ["route", "get", "post", "put", "delete"]):
                            path = "/"
                            method = "GET"
                            if isinstance(dec, ast.Call):
                                if dec.args and isinstance(dec.args[0], ast.Constant):
                                    path = dec.args[0].value
                            if "post" in dec_str.lower(): method = "POST"
                            elif "put" in dec_str.lower(): method = "PUT"
                            elif "delete" in dec_str.lower(): method = "DELETE"
                            routes_found.append({"name": node.name, "path": path, "method": method})

        for r in routes_found[:6]:
            nodes.append({
                "id": f"route_{r['name']}", "type": "Route", "category": "api",
                "title": f"{r['method']} {r['path']}", "shape": [], "shape_label": r['name'] + "()",
                "color": "#ed7d31", "math": "",
                "description": f"API endpoint that handles {r['method']} requests to {r['path']}. Handler function: {r['name']}()."
            })

        # Database detection
        has_db = any(p in all_text for p in [
            "cursor", "session.query", "db.session", ".execute(", "SQLAlchemy",
            "models.", "create_engine", "pymongo", "redis", "psycopg", ".commit()"
        ])
        if has_db:
            db_type = "Redis" if "redis" in all_text.lower() else ("MongoDB" if "mongo" in all_text.lower() else "SQL Database")
            nodes.append({
                "id": "database", "type": "Database", "category": "database",
                "title": "DATABASE", "shape": [], "shape_label": db_type,
                "color": "#ffc000", "math": "",
                "description": f"Persistent {db_type} storage. Stores and retrieves application data."
            })

        # Queue detection
        has_queue = any(p in all_text for p in ["celery", "rabbitmq", "kafka", "SQS", "redis.publish", "task.delay"])
        if has_queue:
            nodes.append({
                "id": "queue", "type": "Queue", "category": "queue",
                "title": "MESSAGE QUEUE", "shape": [], "shape_label": "Async Tasks",
                "color": "#9b59b6", "math": "",
                "description": "Asynchronous task queue for background processing. Decouples producers from consumers."
            })

        # Cache detection
        has_cache = any(p in all_text for p in ["cache", "lru_cache", "redis.get", "memcached"])
        if has_cache:
            nodes.append({
                "id": "cache_node", "type": "Cache", "category": "cache",
                "title": "CACHE", "shape": [], "shape_label": "In-Memory",
                "color": "#00b894", "math": "",
                "description": "In-memory cache for frequently accessed data. Speeds up repeated requests."
            })

        # Response
        nodes.append({
            "id": "response", "type": "Response", "category": "output",
            "title": "RESPONSE", "shape": [200], "shape_label": "HTTP 200 OK",
            "color": "#c00000", "math": "",
            "description": "The server sends back a JSON/HTML response to the client."
        })

        return {"nodes": nodes, "meta": {"type": "web_app"}}

    def _analyze_generic(self, code_files):
        nodes = []
        all_text = "\n".join(code_files.values())

        # Detect data pipeline patterns
        has_pipeline = any(p in all_text for p in ["pandas", "DataFrame", "read_csv", "read_json", "spark", "pipeline"])
        # Detect CLI patterns
        has_cli = any(p in all_text for p in ["argparse", "click", "sys.argv", "typer"])

        # Entry point
        nodes.append({
            "id": "start", "type": "Start", "category": "input",
            "title": "INPUT", "shape": [1, 28, 28] if not has_pipeline else [],
            "shape_label": "Entry Point",
            "color": "#4472c4", "math": "",
            "description": "The program begins execution. Imports are resolved and initial setup runs."
        })

        if has_cli:
            nodes.append({
                "id": "cli", "type": "CLI", "category": "client",
                "title": "CLI PARSER", "shape": [], "shape_label": "Arguments",
                "color": "#a5a5a5", "math": "",
                "description": "Parses command-line arguments and flags provided by the user."
            })

        # Scan for classes and functions
        classes_found = []
        funcs_found = []
        for fname, code in code_files.items():
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
                    classes_found.append({"name": node.name, "file": fname, "methods": methods})
                elif isinstance(node, ast.FunctionDef) and node.name not in ("__init__", "__str__", "__repr__", "__len__", "__getitem__"):
                    if not node.name.startswith("_"):
                        funcs_found.append({"name": node.name, "file": fname, "lineno": node.lineno})

        # Add classes as 3D server/generic blocks
        for cls in classes_found[:6]:
            methods_str = ", ".join(cls["methods"][:4])
            nodes.append({
                "id": f"class_{cls['name']}", "type": "Class", "category": "server",
                "title": cls["name"].upper(), "shape": [],
                "shape_label": f"{len(cls['methods'])} methods",
                "color": "#5b9bd5", "math": "",
                "description": f"Class '{cls['name']}' defined in {cls['file']}. Methods: {methods_str or 'none'}.",
                "params_label": f"file={cls['file']}"
            })

        # Add functions
        for func in funcs_found[:8]:
            nodes.append({
                "id": f"func_{func['name']}", "type": "Function", "category": "api",
                "title": func["name"].upper() + "()", "shape": [],
                "shape_label": f"line {func['lineno']}",
                "color": "#70ad47", "math": "",
                "description": f"Function '{func['name']}()' defined in {func['file']} at line {func['lineno']}.",
                "params_label": f"file={func['file']}"
            })

        # Data pipeline components
        if has_pipeline:
            if "read_csv" in all_text or "read_json" in all_text:
                nodes.append({
                    "id": "data_load", "type": "DataLoad", "category": "database",
                    "title": "LOAD DATA", "shape": [], "shape_label": "CSV/JSON",
                    "color": "#ffc000", "math": "",
                    "description": "Reads data from files (CSV, JSON, Parquet, etc.) into memory."
                })
            if "transform" in all_text.lower() or "apply" in all_text or "map" in all_text:
                nodes.append({
                    "id": "transform", "type": "Transform", "category": "cache",
                    "title": "TRANSFORM", "shape": [], "shape_label": "Processing",
                    "color": "#00b894", "math": "",
                    "description": "Applies data transformations: filtering, mapping, aggregating."
                })

        # File I/O detection
        if "open(" in all_text or "write(" in all_text or "json.dump" in all_text:
            nodes.append({
                "id": "file_io", "type": "FileIO", "category": "database",
                "title": "FILE I/O", "shape": [], "shape_label": "Read/Write",
                "color": "#ed7d31", "math": "",
                "description": "Reads from or writes to files on disk."
            })

        # End
        nodes.append({
            "id": "end", "type": "End", "category": "output",
            "title": "OUTPUT", "shape": [],
            "shape_label": "Result",
            "color": "#c00000", "math": "",
            "description": "The program produces its final output and exits."
        })

        return {"nodes": nodes[:20], "meta": {"type": "generic"}}

    def _empty(self):
        return {"nodes": [{
            "id": "empty", "type": "Empty", "category": "other",
            "title": "NO CODE FOUND", "shape": [],
            "shape_label": "", "color": "#ff6348",
            "description": "No Python files found in the uploaded ZIP.", "math": ""
        }], "meta": {"type": "empty"}}

