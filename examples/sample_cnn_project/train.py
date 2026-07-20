"""Training script for the Image Classifier."""
import torch
import torch.nn as nn
import torch.optim as optim
from model import ImageClassifier


def train(model, dataloader, epochs=10):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(epochs):
        running_loss = 0.0
        for images, labels in dataloader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1}, Loss: {running_loss:.4f}")


if __name__ == "__main__":
    model = ImageClassifier(num_classes=10)
    print(model)
