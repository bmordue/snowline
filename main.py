import argparse
import yaml

def main():
    parser = argparse.ArgumentParser(description="Snowline Visualization Tool")
    parser.add_argument("--config", type=str, required=True,
                        help="Path to the YAML configuration file")
    args = parser.parse_args()

    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        print("Configuration loaded successfully:")
        print(yaml.dump(config, indent=2))
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {args.config}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")

if __name__ == "__main__":
    main()
