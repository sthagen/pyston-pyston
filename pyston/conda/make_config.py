import os
import sys

def replace_section(lines, name, new_str):
    for i in range(len(lines)):
        if lines[i] != name + ":":
            continue

        removed = []
        while i + 1 < len(lines) and lines[i + 1].startswith("- "):
            removed.append(lines[i + 1])
            del lines[i + 1]
        lines.insert(i + 1, new_str)
        return removed

    return False

def rewrite_config(config_str):
    lines = config_str.split('\n')

    removed = replace_section(lines, "python", "- 3.8.* *_pyston")
    assert removed, "Didn't find 'python' line, this might not be a python extension"
    assert "- 3.8.* *_cpython" in removed, ("This might not be the right config? Found:", removed)

    replace_section(lines, "python_impl", "- pyston")

    removed = replace_section(lines, "numpy", "- '1.18'")
    if removed:
        assert any("1.18" in s for s in removed), removed

    return '\n'.join(lines)

def main():
    configs = os.listdir(".ci_support")

    possible_configs = []

    cwd = os.getcwd()

    for c in configs:
        if "aarch64" in c or "ppc" in c:
            continue
        if "win" in c or "osx" in c:
            continue
        if "3." in c and "3.8" not in c:
            continue
        if c in ("migrations", "README"):
            continue
        if "openssl3" in c:
            continue
        if ("mpi4py" in cwd or "h5py" in cwd or "netcdf4" in cwd) and ("openmpi" in c or "nompi" in c):
            continue
        if "nomkl" in c:
            continue
        if "pyproj" in cwd and "8.2.0" not in c:
            continue
        if "paraview" in cwd and "qt" not in c:
            continue
        if "pocl" in cwd and "hwloc1" in c:
            continue

        # Not sure about this, but only build the cpu version of arrow-cpp
        if "arrow-cpp" in cwd:
            if "None" not in c:
                continue
        elif "cuda_compiler_version" in c or "cuda" in cwd:
            assert "11.3" not in c
            if "11.2" not in c:
                continue

        if "pyston" in c:
            continue

        possible_configs.append(c)

    assert len(possible_configs) == 1, possible_configs
    config, = possible_configs

    config_str = open(".ci_support/" + config).read()
    new_config_str = rewrite_config(config_str)

    with open(".ci_support/linux-pyston.yaml", 'w') as f:
        f.write(new_config_str)
    print("linux-pyston")

if __name__ == "__main__":
    try:
        main()
    except:
        print("make_config.py-failed")
        raise
