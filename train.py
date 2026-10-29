
import argparse
import copy
import os
import torch
import torch.nn.functional as F

from model import RayXModel, DEFAULT_CONFIG


DEVICE = torch.device("cpu")


def get_batches(data, block_size, batch_size):
    if len(data) <= block_size + 1:
        raise ValueError("Dataset must exceed block_size + 1 bytes.")

    starts = torch.randint(
        0, len(data) - block_size - 1, (batch_size,)
    )
    x = torch.stack([
        data[i:i + block_size] for i in starts.tolist()
    ])
    y = torch.stack([
        data[i + 1:i + block_size + 1] for i in starts.tolist()
    ])
    return x, y


def evaluate(model, data, block_size, batch_size, batches=5):
    model.eval()
    losses = []

    with torch.no_grad():
        for _ in range(batches):
            x, y = get_batches(data, block_size, batch_size)
            logits = model(x)
            loss = F.cross_entropy(
                logits.reshape(-1, logits.size(-1)),
                y.reshape(-1),
            )
            losses.append(loss.item())

    model.train()
    return sum(losses) / len(losses)


def load_checkpoint(path):
    if not os.path.exists(path):
        return None

    checkpoint = torch.load(
        path, map_location="cpu", weights_only=True
    )

    if not isinstance(checkpoint, dict):
        raise ValueError("Unsupported checkpoint format.")

    state = checkpoint.get("model_state")
    if state is None:
        state = checkpoint.get("model_state_dict")

    if state is None:
        raise ValueError("Checkpoint has no model weights.")

    checkpoint["model_state"] = state
    return checkpoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="train.txt")
    parser.add_argument("--validation", default="validation.txt")
    parser.add_argument(
        "--checkpoint", default="artifacts/rayx_model.pt"
    )
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--save-every", type=int, default=50)
    args = parser.parse_args()

    if min(args.steps, args.batch_size, args.save_every) < 1:
        raise ValueError("Steps, batch-size and save-every must be positive.")

    torch.manual_seed(42)

    train_raw = open(args.train, "rb").read()
    val_raw = open(args.validation, "rb").read()

    train_data = torch.tensor(list(train_raw), dtype=torch.long)
    val_data = torch.tensor(list(val_raw), dtype=torch.long)

    checkpoint = load_checkpoint(args.checkpoint)
    config = dict(DEFAULT_CONFIG)

    if checkpoint:
        config.update(checkpoint.get("config", {}))

    model = RayXModel(config).to(DEVICE)

    if checkpoint:
        try:
            model.load_state_dict(checkpoint["model_state"], strict=True)
        except RuntimeError as exc:
            raise SystemExit(
                "Checkpoint architecture mismatch. Original checkpoint unchanged."
            ) from exc
        print("Loaded previous RayX weights.")
    else:
        print("No checkpoint found; training from scratch.")

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=0.01
    )

    if checkpoint and checkpoint.get("optimizer_state"):
        try:
            optimizer.load_state_dict(checkpoint["optimizer_state"])
            for group in optimizer.param_groups:
                group["lr"] = args.lr
            print("Optimizer state restored.")
        except (ValueError, RuntimeError) as exc:
            print("Using a fresh optimizer:", exc)

    step = int(checkpoint.get("step", 0)) if checkpoint else 0
    block_size = int(config["block_size"])

    if len(train_data) <= block_size + 1:
        raise ValueError("Training dataset is too small.")

    if len(val_data) <= block_size + 1:
        raise ValueError("Validation dataset is too small.")

    best_val = float("inf")
    best_state = None

    model.train()

    for iteration in range(1, args.steps + 1):
        x, y = get_batches(train_data, block_size, args.batch_size)

        logits = model(x)
        loss = F.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            y.reshape(-1),
        )

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        step += 1

        if iteration % 25 == 0 or iteration == 1:
            val_loss = evaluate(
                model, val_data, block_size, args.batch_size
            )
            print(
                f"step={step} train_loss={loss.item():.4f} "
                f"val_loss={val_loss:.4f}"
            )

            if val_loss < best_val:
                best_val = val_loss
                best_state = copy.deepcopy(model.state_dict())

        if iteration % args.save_every == 0 or iteration == args.steps:
            os.makedirs(
                os.path.dirname(args.checkpoint) or ".",
                exist_ok=True,
            )

            torch.save({
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "config": config,
                "step": step,
                "loss": float(loss.item()),
            }, args.checkpoint)

            print("Checkpoint saved:", args.checkpoint)

    if best_state is not None:
        torch.save({
            "model_state": best_state,
            "config": config,
            "step": step,
            "validation_loss": best_val,
        }, "artifacts/rayx_model_best.pt")
        print("Best validation checkpoint saved.")

    print("Training finished.")


if __name__ == "__main__":
    main()
