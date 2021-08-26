import torch
import torch.nn as nn

# %%
class autoencoder(nn.Module):
    def __init__(self, in_channels=500):
        super(autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(in_channels, 16, 1, stride=1),  # b, 16, 240
            nn.ReLU(True),
            nn.MaxPool1d(2, stride=2),  # b, 16, 120
            nn.Conv1d(16, 8, 1, stride=1),  # b, 8, 120
            nn.ReLU(True),
            nn.MaxPool1d(2, stride=2)  # b, 8, 60
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(8, 16, 2, stride=2),  # b, 16, 120
            nn.ReLU(True),
            nn.ConvTranspose1d(16, in_channels, 2, stride=2),  # b, 500, 240
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x


# %%
if __name__ == '__main__':
    batch = 64
    m, n = 500, 240
    x_cube = torch.randn(size=(batch, m, n))
    model = autoencoder(in_channels=500)
    encoder = model.encoder(x_cube)
    print(encoder.shape)
    decoder = model.decoder(encoder)
    print(encoder.shape, decoder.shape)
