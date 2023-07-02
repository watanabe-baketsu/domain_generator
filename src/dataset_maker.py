import os
import json
from argparse import ArgumentParser
from pprint import pprint


def read_dataset(path: str) -> list:
    dataset = []
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            filepath = os.path.join(path, filename)
            with open(filepath, "r") as file:
                content = json.load(file)
            for entry in content:
                if entry["verified"] == "yes" and entry["target"] != "Other" and entry not in dataset:
                    dataset.append(entry)
    return dataset


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--path", type=str, default="datasets/raw")
    args = parser.parse_args()

    phish = read_dataset(args.path)

    with open("datasets/phish.json", "w") as file:
        json.dump(phish, file, indent=4)

    print(f"Phish dataset size: {len(phish)}")

    analysis = {}
    for entry in phish:
        target = entry["target"]
        if target not in analysis:
            analysis[target] = 0
        analysis[target] += 1
    pprint(analysis)
