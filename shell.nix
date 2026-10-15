{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = [pkgs.ruff pkgs.basedpyright];
}
