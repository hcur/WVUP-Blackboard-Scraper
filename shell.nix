{ pkgs ? import <nixpkgs> {} }:

# a nix-shell definition that I use to
# establish an environment in which to run
# the script.

pkgs.mkShell {
  name = "blackboard scraper";
  buildInputs = with pkgs; [
    python3
    python310Packages.beautifulsoup4
    python310Packages.selenium
  ];

  shellHook = ''
            echo "Starting new shell...";
  '';
}
