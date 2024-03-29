#!/usr/bin/env python
"""This script compiles and verifies the output for all form files
found in the 'demo' directory. The verification is performed in two
steps. First, the generated code is compared with stored references.
Then, the output from all functions in the generated code is compared
with stored reference values.

This script can also be used for benchmarking tabulate_tensor for all
form files found in the 'bench' directory. To run benchmarks, use the
option --bench.

"""

# Copyright (C) 2010-2013 Anders Logg, Kristian B. Oelgaard and Marie E. Rognes
#
# This file is part of FFC.
#
# FFC is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FFC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with FFC. If not, see <http://www.gnu.org/licenses/>.
#
# Modified by Martin Alnaes, 2013
# Modified by Johannes Ring, 2013
# Modified by Kristian B. Oelgaard, 2013
# Modified by Garth N. Wells, 2014
#
# First added:  2010-01-21

# FIXME: Need to add many more test cases. Quite a few DOLFIN forms
# failed after the FFC tests passed.

import os, sys, shutil, difflib
from numpy import array, shape, abs, max, isnan
from ffc.log import begin, end, info, info_red, info_green, info_blue
from ufctest import generate_test_code
from instant.output import get_status_output
import time

# Parameters
debug = False # TODO: Can make this a cmdline argument, and start crashing programs in debugger automatically?
output_tolerance = 1.e-6
demo_directory = "../../../../demo"
bench_directory = "../../../../bench"

# Global log file
logfile = None

# Extended quadrature tests (optimisations)
ext_quad = [\
"-r quadrature -O -feliminate_zeros",
"-r quadrature -O -fsimplify_expressions",
"-r quadrature -O -fprecompute_ip_const",
"-r quadrature -O -fprecompute_basis_const",
"-r quadrature -O -fprecompute_ip_const -feliminate_zeros",
"-r quadrature -O -fprecompute_basis_const -feliminate_zeros",
]

# Extended uflacs tests (to be extended with optimisation parameters later)
ext_uflacs = [\
"-r uflacs",
]

_command_timings = []
def run_command(command):
    "Run command and collect errors in log file."
    # Debugging:
    #print "IN DIRECTORY:", os.path.abspath(os.curdir)
    #print "RUNNING COMMAND:", command
    t1 = time.time()
    (status, output) = get_status_output(command)
    t2 = time.time()
    global _command_timings
    _command_timings.append((command, t2-t1))
    if status == 0:
        return True
    global logfile
    if logfile is None:
        logfile = open("../../error.log", "w")
    logfile.write(output + "\n")
    print(output)
    return False

def log_error(message):
    "Log error message."
    global logfile
    if logfile is None:
        logfile = open("../../error.log", "w")
    logfile.write(message + "\n")

def clean_output(output_directory):
    "Clean out old output directory"
    if os.path.isdir(output_directory):
        shutil.rmtree(output_directory)
    os.mkdir(output_directory)

def generate_test_cases(bench, only_forms):
    "Generate form files for all test cases."

    begin("Generating test cases")

    # Copy form files
    if bench:
        form_directory = bench_directory
    else:
        form_directory = demo_directory

    # Make list of form files
    form_files = [f for f in os.listdir(form_directory) if f.endswith(".ufl")]
    if only_forms:
        form_files = [f for f in form_files if f in only_forms]
    form_files.sort()

    for f in form_files:
        shutil.copy("%s/%s" % (form_directory, f), ".")
    info_green("Found %d form files" % len(form_files))

    # Generate form files for forms
    info("Generating form files for extra forms: Not implemented")

    # Generate form files for elements
    if not bench:
        from elements import elements
        info("Generating form files for extra elements (%d elements)" % len(elements))
        for (i, element) in enumerate(elements):
            open("X_Element%d.ufl" % i, "w").write("element = %s" % element)

    end()

def generate_code(args, only_forms):
    "Generate code for all test cases."

    # Get a list of all files
    form_files = [f for f in os.listdir(".") if f.endswith(".ufl")]
    if only_forms:
        form_files = [f for f in form_files if f in only_forms]
    form_files.sort()

    begin("Generating code (%d form files found)" % len(form_files))

    # TODO: Parse additional options from .ufl file? I.e. grep for
    # some sort of tag like '#ffc: <flags>'.
    special = {
        "AdaptivePoisson.ufl": "-e",
        }

    # Iterate over all files
    for f in form_files:
        options = special.get(f, "")

        cmd = ("ffc %s %s -f precision=8 -fconvert_exceptions_to_warnings %s"
               % (options, " ".join(args), f))

        # Generate code
        ok = run_command(cmd)

        # Check status
        if ok:
            info_green("%s OK" % f)
        else:
            info_red("%s failed" % f)

    end()

def validate_code(reference_dir):
    "Validate generated code against references."

    # Get a list of all files
    header_files = [f for f in os.listdir(".") if f.endswith(".h")]
    header_files.sort()

    begin("Validating generated code (%d header files found)" % len(header_files))

    # Iterate over all files
    for f in header_files:

        # Get generated code
        generated_code = open(f).read()

        # Get reference code
        reference_file = os.path.join(reference_dir, f)
        if os.path.isfile(reference_file):
            reference_code = open(reference_file).read()
        else:
            info_blue("Missing reference for %s" % reference_file)
            continue

        # Compare with reference
        if generated_code == reference_code:
            info_green("%s OK" % f)
        else:
            info_red("%s differs" % f)
            diff = "\n".join([line for line in difflib.unified_diff(reference_code.split("\n"), generated_code.split("\n"))])
            s = ("Code differs for %s, diff follows (reference first, generated second)"
                 % os.path.join(*reference_file.split(os.path.sep)[-3:]))
            log_error("\n" + s + "\n" + len(s)*"-")
            log_error(diff)

    end()

def build_programs(bench, permissive):
    "Build test programs for all test cases."

    # Get a list of all files
    header_files = [f for f in os.listdir(".") if f.endswith(".h")]
    header_files.sort()

    begin("Building test programs (%d header files found)" % len(header_files))

    # Get UFC flags
    ufc_cflags = get_status_output("pkg-config --cflags ufc-1")[1].strip()

    # Get Boost dir (code copied from ufc/src/utils/python/ufc_utils/build.py)
    # Set a default directory for the boost installation
    if sys.platform == "darwin":
        # Use Brew as default
        default = os.path.join(os.path.sep, "usr", "local")
    else:
        default = os.path.join(os.path.sep, "usr")

    # If BOOST_DIR is not set use default directory
    boost_inc_dir = ""
    boost_lib_dir = ""
    boost_math_tr1_lib = "boost_math_tr1"
    boost_dir = os.getenv("BOOST_DIR", default)
    boost_is_found = False
    for inc_dir in ["", "include"]:
        if os.path.isfile(os.path.join(boost_dir, inc_dir, "boost", "version.hpp")):
            boost_inc_dir = os.path.join(boost_dir, inc_dir)
            break
    for lib_dir in ["", "lib", "lib/x86_64-linux-gnu"]:
        for ext in [".so", "-mt.so", ".dylib", "-mt.dylib"]:
            _lib = os.path.join(boost_dir, lib_dir, "lib" + boost_math_tr1_lib + ext)
            if os.path.isfile(_lib):
                if "-mt" in _lib:
                    boost_math_tr1_lib += "-mt"
                boost_lib_dir = os.path.join(boost_dir, lib_dir)
                break
    if boost_inc_dir != "" and boost_lib_dir != "":
        boost_is_found = True

    if not boost_is_found:
        raise OSError("""The Boost library was not found.
If Boost is installed in a nonstandard location,
set the environment variable BOOST_DIR.
""")

    ufc_cflags += " -I%s -L%s" % (boost_inc_dir, boost_lib_dir)

    # Set compiler options
    compiler_options = "%s -Wall" % ufc_cflags
    if not permissive:
        compiler_options += " -Werror -pedantic"
    if bench:
        info("Benchmarking activated")
        # Takes too long to build with -O2
        #compiler_options += " -O2"
        compiler_options += " -O3"
        #compiler_options += " -O3 -fno-math-errno -march=native"
    if debug:
        info("Debugging activated")
        compiler_options += " -g -O0"
    info("Compiler options: %s" % compiler_options)

    # Iterate over all files
    for f in header_files:

        # Generate test code
        filename = generate_test_code(f)

        # Compile test code
        prefix = f.split(".h")[0]
        command = "g++ %s -o %s.bin %s.cpp -l%s" % \
                  (compiler_options, prefix, prefix, boost_math_tr1_lib)
        ok = run_command(command)

        # Check status
        if ok:
            info_green("%s OK" % prefix)
        else:
            info_red("%s failed" % prefix)

    end()

def run_programs(bench):
    "Run generated programs."

    # This matches argument parsing in the generated main files
    bench = 'b' if bench else ''

    # Get a list of all files
    test_programs = [f for f in os.listdir(".") if f.endswith(".bin")]
    test_programs.sort()

    begin("Running generated programs (%d programs found)" % len(test_programs))

    # Iterate over all files
    for f in test_programs:

        # Compile test code
        prefix = f.split(".bin")[0]
        try:
            os.remove(prefix + ".out")
        except:
            pass
        ok = run_command(".%s%s.bin %s > %s.out" % (os.path.sep, prefix, bench, prefix))

        # Check status
        if ok:
            info_green("%s OK" % f)
        else:
            info_red("%s failed" % f)

    end()

def validate_programs(reference_dir):
    "Validate generated programs against references."

    # Get a list of all files
    output_files = [f for f in os.listdir(".") if f.endswith(".json")]
    output_files.sort()

    begin("Validating generated programs (%d programs found)" % len(output_files))

    # Iterate over all files
    for f in output_files:

        # Get generated output
        generated_output = open(f).read()

        # Get reference output
        reference_file = os.path.join(reference_dir, f)
        if os.path.isfile(reference_file):
            reference_output = open(reference_file).read()
        else:
            info_blue("Missing reference for %s" % reference_file)
            continue

        # Compare with reference
        ok = True
        old = [line.split(" = ") for line in reference_output.split("\n") if " = " in line]
        new = dict([line.split(" = ") for line in generated_output.split("\n") if " = " in line])
        header = ("Output differs for %s, diff follows (reference first, generated second)"
                  % os.path.join(*reference_file.split(os.path.sep)[-3:]))
        for (key, value) in old:

            # Check if value is present
            if not key in new:
                if ok: log_error("\n" + header + "\n" + len(header)*"-")
                log_error("%s: missing value in generated code" % key)
                ok = False
                continue

            # Extract float values
            old_values = array([float(v) for v in value.split(" ")])
            new_values = array([float(v) for v in new[key].split(" ")])

            # Check that shape is correct
            if not shape(old_values) == shape(new_values):
                if ok: log_error("\n" + header + "\n" + len(header)*"-")
                log_error("%s: shape mismatch" % key)
                ok = False
                continue

            # Check that values match to within tolerance set by 'output_tolerance'
            diff = max(abs(old_values - new_values))
            if diff > output_tolerance or isnan(diff):
                if ok: log_error("\n" + header + "\n" + len(header)*"-")
                log_error("%s: values differ, error = %g (tolerance = %g)" % (key, diff, output_tolerance))
                log_error("  old = " + " ".join("%.16g" % v for v in old_values))
                log_error("  new = " + " ".join("%.16g" % v for v in new_values))
                ok = False

        # Add debugging output to log file
        debug = "\n".join([line for line in generated_output.split("\n") if "debug" in line])
        if debug: log_error(debug)

        # Check status
        if ok:
            info_green("%s OK" % f)
        else:
            info_red("%s differs" % f)


        # Now check json references
        fj = f.replace(".out", ".json")

        # Get generated json output
        if os.path.exists(fj):
            generated_json_output = open(fj).read()
            if "nan" in generated_json_output:
                info_red("Found nan in generated json output, replacing with 999 to be able to parse as python dict.")
                generated_json_output = generated_json_output.replace("nan", "999")
        else:
            generated_json_output = "{}"

        # Get reference json output
        reference_json_file = os.path.join(reference_dir, fj)
        if os.path.isfile(reference_json_file):
            reference_json_output = open(reference_json_file).read()
        else:
            info_blue("Missing reference for %s" % reference_json_file)
            reference_json_output = "{}"

        # Compare json with reference using recursive diff algorithm
        # TODO: Write to different error file?
        from recdiff import recdiff, print_recdiff, DiffEqual
        # Assuming reference is well formed
        reference_json_output = eval(reference_json_output)
        try:
            generated_json_output = eval(generated_json_output)
        except Exception as e:
            info_red("Failed to evaluate json output for %s" % fj)
            log_error(str(e))
            generated_json_output = None
        json_diff = (None if generated_json_output is None else
                     recdiff(generated_json_output, reference_json_output, tolerance=output_tolerance))
        json_ok = json_diff == DiffEqual

        # Check status
        if json_ok:
            info_green("%s OK" % fj)
        else:
            info_red("%s differs" % fj)
            log_error("Json output differs for %s, diff follows (generated first, reference second)"
                      % os.path.join(*reference_json_file.split(os.path.sep)[-3:]))
            print_recdiff(json_diff, printer=log_error)

    end()

def main(args):
    "Run all regression tests."

    # Check command-line arguments TODO: Use getargs or something
    generate_only  = "--generate-only" in args
    fast           = "--fast" in args
    bench          = "--bench" in args
    use_quad       = "--skip-quad" not in args
    use_ext_quad   = "--ext-quad" in args
    use_ext_uflacs = "--ext-uflacs" in args
    permissive     = "--permissive" in args
    tolerant       = "--tolerant" in args
    print_timing   = "--print-timing" in args
    skip_download  = "--skip-download" in args

    flags = (
        "--generate-only",
        "--fast",
        "--bench",
        "--skip-quad",
        "--ext-quad",
        "--ext-uflacs",
        "--permissive",
        "--tolerant",
        "--print-timing",
        "--skip-download",
        )
    args = [arg for arg in args if not arg in flags]

    # Extract .ufl names from args
    only_forms = set([arg for arg in args if arg.endswith(".ufl")])
    args = [arg for arg in args if arg not in only_forms]

    # Download reference data
    if skip_download:
        info_blue("Skipping reference data download")
    else:
        failure, output = get_status_output("./scripts/download")
        print(output)
        if failure:
            info_red("Download reference data failed")
        else:
            info_green("Download reference data ok")

    if tolerant:
        global output_tolerance
        output_tolerance = 1e-3

    # Clean out old output directory
    output_directory = "output"
    clean_output(output_directory)
    os.chdir(output_directory)

    # Adjust which test cases (combinations of compile arguments) to
    # run here
    test_cases = ["-r auto"]
    if use_quad and (not bench and not fast):
        test_cases += ["-r quadrature", "-r quadrature -O"]
    if use_ext_quad:
        test_cases += ext_quad
    if use_ext_uflacs:
        test_cases = ext_uflacs
        test_cases += ["-r quadrature"]
        #test_cases += ["-r quadrature -O"]

    for argument in test_cases:

        begin("Running regression tests with %s" % argument)

        # Clear and enter output sub-directory
        sub_directory = "_".join(argument.split(" ")).replace("-", "")
        clean_output(sub_directory)
        os.chdir(sub_directory)

        # Generate test cases
        generate_test_cases(bench, only_forms)

        # Generate code
        generate_code(args + [argument], only_forms)

        # Location of reference directories
        reference_directory =  os.path.abspath("../../ffc-reference-data/")
        code_reference_dir = os.path.join(reference_directory, sub_directory)

        # Note: We use the r_auto references for all test cases. This
        # ensures that we continously test that the codes generated by
        # all different representations are equivalent.
        output_reference_dir = os.path.join(reference_directory, "r_auto")

        # Validate code by comparing to code generated with this set
        # of compiler parameters
        if not bench and argument not in ext_quad:
            validate_code(code_reference_dir)

        # Build and run programs and validate output to common
        # reference
        if fast or generate_only:
            info("Skipping program validation")
        elif bench:
            build_programs(bench, permissive)
            run_programs(bench)
        else:
            build_programs(bench, permissive)
            run_programs(bench)
            validate_programs(output_reference_dir)

        # Go back up
        os.chdir(os.path.pardir)

        end()

    # Print results
    if print_timing:
        timings = '\n'.join("%10.2e s  %s" % (t, name) for (name, t) in _command_timings)
        info_green("Timing of all commands executed:")
        info(timings)
    if logfile is None:
        info_green("Regression tests OK")
        return 0
    else:
        info_red("Regression tests failed")
        info("Error messages stored in error.log")
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
