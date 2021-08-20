import runez

from portable_python.builder import BuildSetup, ModuleBuilder


class TclTkModule(ModuleBuilder):
    """Common Tcl/Tk stuff"""

    telltale = ["{include}/tk", "{include}/tk.h"]

    @property
    def version(self):
        return "8.6.10"

    def c_configure_args(self):
        yield from super().c_configure_args()
        yield "--enable-threads"


@BuildSetup.module_builders.declare
class Tcl(TclTkModule):

    @property
    def url(self):
        return f"https://prdownloads.sourceforge.net/tcl/tcl{self.version}-src.tar.gz"

    def _do_linux_compile(self):
        for path in BuildSetup.ls_dir(self.build_folder / "pkgs"):
            if path.name.startswith(("sqlite", "tdbc")):
                # Remove packages we don't care about and can pull in unwanted symbols
                runez.delete(path)

        with runez.CurrentFolder("unix"):
            self.run_configure()
            self.run("make")
            self.run("make", "install", "DESTDIR=%s" % self.deps.parent)
            self.run("make", "install-private-headers", "DESTDIR=%s" % self.deps.parent)


@BuildSetup.module_builders.declare
class Tk(TclTkModule):

    @property
    def url(self):
        return f"https://prdownloads.sourceforge.net/tcl/tk{self.version}-src.tar.gz"

    def c_configure_args(self):
        yield from super().c_configure_args()
        yield f"--with-tcl={self.deps}/lib"
        if self.target.is_macos:
            yield "--enable-aqua=yes"
            yield "--without-x"

        else:
            yield f"--x-includes={self.deps}/include"
            yield f"--x-libraries={self.deps}/lib"

    def _do_linux_compile(self):
        with runez.CurrentFolder("unix"):
            self.run_configure()
            self.run("make")
            self.run("make", "install", "DESTDIR=%s" % self.deps.parent)
            self.run("make", "install-private-headers", "DESTDIR=%s" % self.deps.parent)


@BuildSetup.module_builders.declare
class Tix(TclTkModule):

    c_configure_program = "/bin/sh configure"

    @property
    def url(self):
        return f"https://github.com/python/cpython-source-deps/archive/tix-{self.version}.tar.gz"

    @property
    def version(self):
        return "8.4.3.6"

    def xenv_cflags(self):
        # Needed to avoid error: Getting no member named 'result' in 'struct Tcl_Interp'
        yield "-DUSE_INTERP_RESULT"

    def c_configure_args(self):
        yield from super().c_configure_args()
        yield f"--with-tcl={self.deps}/lib"
        yield f"--with-tk={self.deps}/lib"
        if self.target.is_macos:
            yield "--without-x"

        else:
            yield f"--x-includes={self.deps}/include"
            yield f"--x-libraries={self.deps}/lib"

    def _do_linux_compile(self):
        self.run_configure()
        self.run("make")
        self.run("make", "install", "DESTDIR=%s" % self.deps.parent)
