
import torch
import torch.nn as nn


DEFAULT_CONFIG = {
    "vocab_size": 256,
    "block_size": 128,
    "d_model": 128,
    "n_heads": 4,
    "n_layers": 4,
    "dropout": 0.1,
}


class RayXModel(nn.Module):
    """Byte-level autoregressive Transformer."""

    def __init__(self, config=None):
        super().__init__()

        self.config = {**DEFAULT_CONFIG, **(config or {})}

        vocab = int(self.config["vocab_size"])
        block = int(self.config["block_size"])
        width = int(self.config["d_model"])
        heads = int(self.config["n_heads"])
        layers = int(self.config["n_layers"])
        dropout = float(self.config["dropout"])

        if width % heads:
            raise ValueError("d_model must be divisible by n_heads")

        # Keep these layer names stable for future checkpoints.
        self.token_embedding = nn.Embedding(vocab, width)
        self.position_embedding = nn.Embedding(block, width)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=width,
            nhead=heads,
            dim_feedforward=4 * width,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=False,
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=layers,
            enable_nested_tensor=False,
        )

        self.ln_f = nn.LayerNorm(width)
        self.lm_head = nn.Linear(width, vocab, bias=False)

        # Weight tying reduces parameters.
        self.lm_head.weight = self.token_embedding.weight

    def forward(self, idx):
        batch, length = idx.shape

        if length > self.config["block_size"]:
            raise ValueError("Input exceeds block_size")

        positions = torch.arange(length, device=idx.device)
        x = self.token_embedding(idx)
        x = x + self.position_embedding(positions)[None, :, :]

        # Prevent each position from seeing future bytes.
        causal_mask = torch.triu(
            torch.ones(
                length, length,
                device=idx.device,
                dtype=torch.bool,
            ),
            diagonal=1,
        )

        x = self.transformer(x, mask=causal_mask)
        x = self.ln_f(x)
        return self.lm_head(x)


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
