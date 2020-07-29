#!/usr/bin/env python
import json
import os
import subprocess
from urllib.parse import urlparse

REGIONS = {
    "af-south-1": "Cape Town (Africa)",
    "ap-east-1": "Hong Kong (Asia)",
    "ap-northeast-1": "Tokyo (Asia)",
    "ap-northeast-2": "Seoul (Asia)",
    "ap-northeast-3": "Osaka (Asia)",
    "ap-south-1": "Mumbai (Asia)",
    "ap-southeast-1": "Singapore (Asia)",
    "ap-southeast-2": "Sydney (Australia)",
    "ca-central-1": "Canada",
    "cn-north-1": "Beijing (Asia)",
    "cn-northwest-1": "Ningxia (Asia)",
    "eu-central-1": "Frankfurt (Europe)",
    "eu-north-1": "Stockholm (Europe)",
    "eu-south-1": "Milan (Europe)",
    "eu-west-1": "Ireland (Europe)",
    "eu-west-2": "London (Europe)",
    "eu-west-3": "Paris (Europe)",
    "me-south-1": "Bahrain (Middle East)",
    "sa-east-1": "São Paulo (South America)",
    "us-east-1": "N. Virginia (US)",
    "us-east-2": "Ohio (US)",
    "us-west-1": "N. California (US)",
    "us-west-2": "Oregon (US)",
}


def run(regions):
    urls = []

    for i, region in enumerate(regions):
        location = REGIONS[region]
        print(f"{i + 1} ATTEMPTING", region, location)
        os.environ["AWS_DEFAULT_REGION"] = region
        os.environ["DEBUG"] = "false"
        r = subprocess.run(
            "chalice deploy --profile relayer".split(),
            # "./dummy.sh".split(),
            capture_output=True,
        )
        stdout = r.stdout.decode("utf-8")
        stderr = r.stderr.decode("utf-8")
        if not r.returncode:
            for line in stdout.splitlines():
                if "Rest API URL:" in line:
                    urls.append(line.split("Rest API URL:")[1].strip())
                    print(f"SUCCESS ({i + 1} of {len(REGIONS)}):", region, urls[-1])
                    break
            else:
                print(stdout)
                raise ValueError("'Rest API URL:' not found")
        elif "UnrecognizedClientException" in stderr:
            # https://github.com/aws/chalice/issues/1445
            print(f"FAILED ({i + 1} of {len(REGIONS)}):", region)
        else:
            print("EXIT:", r.returncode)
            if stdout:
                print("OUTPUT:")
                print(stdout)
            if stderr:
                print("ERROR:")
                print(stderr)
            # raise Exception("Unexpected error")

    if urls:
        print("\nFINISHED LIST OF URLS...(in JSON)\n")
        print(json.dumps(urls, indent=4))
        print("\n")
        print("FINISHED LIST OF URLS...(in PYTHON)\n")
        print("[")
        for url in urls:
            region = urlparse(url).netloc.split(".")[-3]
            name = REGIONS[region]
            print(f'    "{url}",  # {name}')
        print("]")
        print("")
    else:
        raise Exception("No URLs found")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "regions", help="Specific regions (default: all)", nargs="*",
    )
    args = parser.parse_args()
    for region in args.regions:
        if region not in REGIONS:
            raise Exception(f"{region!r} is not a valid region")

    run(args.regions or list(REGIONS.keys()))


if __name__ == "__main__":
    import sys

    sys.exit(main())
