{
  description = "A development environment for the Snowline Visualization Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
    };
  in {
    devShells.${system}.default = pkgs.mkShell {
      name = "snowline-env";
      buildInputs = with pkgs; [
        (python3.withPackages (ps: with ps; [
          geopandas
          rasterio
          matplotlib
          cartopy
          pyyaml
          shapely
          numpy
          scipy
          scikit-image
          pytest
        ]))
        # Add other system dependencies here if needed
      ];

      shellHook = ''
        echo "Entering Snowline Visualization Tool development environment..."
        export PYTHONPATH=$(pwd)
      '';
    };
  };
}
