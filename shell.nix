{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.virtualenv
    pkgs.z3
  ];

  shellHook = ''
    # Create a virtual environment
    # Check if the virtual environment already exists
    if [ ! -d "./bin/" ]; then
      echo "Creating a new virtual environment."
      virtualenv .
    else
      echo "Virtual environment already exists."
    fi

    source ./bin/activate

    pip install -r ./requirements.txt
    result=$(pysmt-install | grep -c z3)

    if [ $result -gt 1 ]; then
      echo 'z3 already installed'
    else
        pysmt-install --z3
    fi
  '';
}
