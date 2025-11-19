with import <nixpkgs> {};

pkgs.mkShell {
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
    ]))
    # Add other system dependencies here if needed
  ];

  shellHook = ''
    echo "Entering Snowline Visualization Tool development environment..."
    export PYTHONPATH=$(pwd)
  '';
}
