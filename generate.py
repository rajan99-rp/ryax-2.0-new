
import torch
import torch.nn.functional as F
from model import RayXModel, DEFAULT_CONFIG

CHECKPOINT_PATH = "artifacts/rayx_model.pt"
END_MARKER = b"### End"


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    checkpoint = torch.load(
        CHECKPOINT_PATH,
        map_location=device,
        weights_only=True,
    )

    config = dict(DEFAULT_CONFIG)
    config.update(checkpoint.get("config", {}))

    model = RayXModel(config).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    block_size = int(config["block_size"])

    print("\nRayX Model 2.0 is running!")
    print("Type 'exit' to stop.\n")

    while True:
        prompt = input("You: ").strip()

        if prompt.lower() in ("exit", "quit"):
            print("RayX stopped.")
            break

        if not prompt:
            continue

        # Match the format used in the training dataset.
        prefix = f"### User: {prompt}\n### RayX:"
        prompt_bytes = prefix.encode("utf-8")

        input_ids = torch.tensor(
            list(prompt_bytes),
            dtype=torch.long,
            device=device,
        ).unsqueeze(0)

        generated = []

        with torch.no_grad():
            for _ in range(400):
                context = input_ids[:, -block_size:]
                logits = model(context)
                next_logits = logits[:, -1, :].clone()

                temperature = 0.8
                next_logits /= temperature

                top_k = min(40, next_logits.size(-1))
                values, _ = torch.topk(next_logits, top_k)
                cutoff = values[:, [-1]]
                next_logits[next_logits < cutoff] = float("-inf")

                probs = F.softmax(next_logits, dim=-1)
                next_token = torch.multinomial(probs, 1)

                token = int(next_token.item())
                generated.append(token)
                input_ids = torch.cat(
                    [input_ids, next_token], dim=1
                )

                # Stop at the conversation end marker.
                if bytes(generated).endswith(END_MARKER):
                    break

        response_bytes = bytes(generated)

        if END_MARKER in response_bytes:
            response_bytes = response_bytes.split(
                END_MARKER, 1
            )[0]

        response = response_bytes.decode(
            "utf-8", errors="replace"
        ).strip()

        # Hide a repeated response header if the model generates one.
        if response.startswith("### RayX:"):
            response = response[len("### RayX:"):].strip()

        print("RayX:", response or "(No response generated)", "\n")


if __name__ == "__main__":
    main()
