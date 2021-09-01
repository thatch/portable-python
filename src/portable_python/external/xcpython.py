import os

import runez

from portable_python import ModuleBuilder


class Bdb(ModuleBuilder):
    """See https://docs.python.org/3/library/dbm.html"""

    m_build_cwd = "build_unix"
    m_telltale = None  # "{include}/ndbm.h" # Builds OK (statically) if libgdbm-compat-dev is present

    @property
    def url(self):
        return f"https://ftp.osuosl.org/pub/blfs/conglomeration/db/db-{self.version}.tar.gz"

    @property
    def version(self):
        return "6.2.32"

    def xenv_CFLAGS(self):
        yield "-fPIC"

    def _do_linux_compile(self):
        self.run_configure("../dist/configure", "--enable-shared=no", "--enable-static=yes", "--enable-dbm", "--with-pic=yes")
        self.run_make()
        self.run_make("install")


class Bzip2(ModuleBuilder):
    """
    See https://docs.python.org/3/library/bz2.html
    """

    m_telltale = "{include}/bzlib.h"

    @property
    def url(self):
        return f"https://sourceware.org/pub/bzip2/bzip2-{self.version}.tar.gz"

    @property
    def version(self):
        return "1.0.8"

    def _do_linux_compile(self):
        self.run_make("install", f"PREFIX={self.deps}", "CFLAGS=-fPIC -O2 -g -D_FILE_OFFSET_BITS=64")


class Gdbm(ModuleBuilder):
    """See https://docs.python.org/2.7/library/gdbm.html"""

    m_telltale = "{include}/gdbm.h"  # Need it on macos too, otherwise a brew install from /usr/local is picked up

    @property
    def url(self):
        return f"https://ftp.gnu.org/gnu/gdbm/gdbm-{self.version}.tar.gz"

    @property
    def version(self):
        return "1.18.1"

    def _do_linux_compile(self):
        self.run_configure(
            "./configure",
            "--enable-shared=no",
            "--enable-static=yes",
            "--with-pic=yes",
            "--enable-libgdbm-compat",
            "--disable-dependency-tracking",
            "--disable-silent-rules",
            "--disable-rpath",
            "--without-libiconv-prefix",
            "--without-libintl-prefix",
            "--without-readline",
        )
        self.run_make()
        self.run_make("install")
        runez.move(self.deps / "include/ndbm.h", self.deps / "include/gdbm-ndbm.h")


class LibFFI(ModuleBuilder):

    m_telltale = ["{include}/ffi.h", "{include}/ffi/ffi.h"]

    def auto_use_with_reason(self):
        if self.target.is_macos:
            return False, runez.blue("on demand on macos")

        if self.target.is_linux:
            path = self._find_telltale(self.m_telltale)
            if path:
                return True, "%s (on top of libffi-dev)" % runez.green("needed on linux")  # pragma: no cover, provisional

        return super().auto_use_with_reason()

    @property
    def url(self):
        return f"https://github.com/libffi/libffi/releases/download/v{self.version}/libffi-{self.version}.tar.gz"

    @property
    def version(self):
        return "3.3"

    def xenv_CFLAGS(self):
        yield "-fPIC"

    def _do_linux_compile(self):
        self.run_configure(
            "./configure",
            "--enable-shared=no",
            "--enable-static=yes",
            "--with-pic=yes",
            self.target.is_macos and "--disable-multi-os-directory",
            "--disable-docs",
        )
        self.run_make()
        self.run_make("install")


class Openssl(ModuleBuilder):

    m_telltale = "{include}/openssl/ssl.h"

    @property
    def url(self):
        return f"https://www.openssl.org/source/openssl-{self.version}.tar.gz"

    @property
    def version(self):
        return "1.1.1k"

    def c_configure_args(self):
        yield f"--openssldir={self.deps}"
        yield "-DPEDANTIC"
        yield "no-shared", "no-idea", "no-tests"
        if self.target.is_macos:
            yield "darwin64-%s-cc" % self.target.architecture

        else:
            yield "%s-%s" % (self.target.platform, self.target.architecture)

    def _do_linux_compile(self):
        self.run_configure("./Configure", self.c_configure_args())
        self.run_make("depend")
        self.run_make("all")
        self.run_make("install_sw")  # See https://github.com/openssl/openssl/issues/8170


class Ncurses(ModuleBuilder):

    @property
    def url(self):
        return f"https://ftp.gnu.org/pub/gnu/ncurses/ncurses-{self.version}.tar.gz"

    @property
    def version(self):
        return "6.2"

    def _do_linux_compile(self):
        self.run_configure(
            "./configure", "--enable-shared=no", "--enable-static=yes", "--enable-widec"
            "--without-cxx", "--without-tests", "--without-manpages", "--disable-stripping"
        )
        self.run_make()
        self.run_make("install")


class Readline(ModuleBuilder):
    """See https://github.com/Homebrew/homebrew-core/blob/HEAD/Formula/readline.rb"""

    m_telltale = "{include}/readline/readline.h"

    @classmethod
    def candidate_modules(cls):
        return [Ncurses]

    @property
    def url(self):
        return f"https://ftp.gnu.org/gnu/readline/readline-{self.version}.tar.gz"

    @property
    def version(self):
        return "8.1"

    def _do_linux_compile(self):
        self.run_configure("./configure", "--enable-shared=no", "--enable-static=yes", "--disable-install-examples", "--with-curses")
        self.run_make()
        self.run_make("install")


class Sqlite(ModuleBuilder):

    m_telltale = "{include}/sqlite3.h"

    def auto_use_with_reason(self):
        if self.target.is_macos:
            return False, runez.blue("on demand on macos")

        if not runez.which("tclsh"):
            return None, runez.brown("requires tclsh")

        if self.target.is_linux:
            path = self._find_telltale(self.m_telltale)
            if path:
                return True, "%s (on top of libsqlite3-dev)" % runez.green("needed on linux")  # pragma: no cover, provisional

            # TODO: fails to link on linux without libsqlite3-dev (works correctly if present)
            return False, runez.red("need libsqlite3-dev on linux as well, pending enhancement")

        return super().auto_use_with_reason()

    @property
    def url(self):
        return f"https://github.com/sqlite/sqlite/archive/refs/tags/version-{self.version}.tar.gz"

    @property
    def version(self):
        return "3.36.0"

    def xenv_CFLAGS(self):
        yield "-fPIC"

    def _do_linux_compile(self):
        self.run_configure(
            "./configure", "--enable-shared=no", "--enable-static=yes", "--disable-tcl", "--disable-readline", "--with-pic=yes"
        )
        self.run_make()
        self.run_make("install")


class Tcl(ModuleBuilder):

    m_build_cwd = "unix"

    @property
    def url(self):
        return f"https://prdownloads.sourceforge.net/tcl/tcl{self.version}-src.tar.gz"

    def _prepare(self):
        for path in runez.ls_dir(self.m_src_build / "pkgs"):
            if path.name.startswith(("sqlite", "tdbc")):
                # Remove packages we don't care about and can pull in unwanted symbols
                runez.delete(path)

    def _do_linux_compile(self):
        self.run_configure("./configure", "--enable-shared=no", "--enable-threads")
        self.run_make()
        self.run_make("install")
        self.run_make("install-private-headers")


class Tk(ModuleBuilder):

    m_build_cwd = "unix"

    @property
    def url(self):
        return f"https://prdownloads.sourceforge.net/tcl/tk{self.version}-src.tar.gz"

    def xenv_CFLAGS(self):
        yield self.checked_deps_folder("include", prefix="-I")

    def xenv_LDFLAGS(self):
        yield f"-L{self.deps_lib}"

    def c_configure_args(self):
        yield "--enable-shared=no"
        yield "--enable-threads"
        yield f"--with-tcl={self.deps_lib}"
        yield "--without-x"
        if self.target.is_macos:
            yield "--enable-aqua=yes"

    def _do_linux_compile(self):
        self.run_configure("./configure", self.c_configure_args())
        self.run_make()
        runez.touch("wish")
        self.run_make("install")
        self.run_make("install-private-headers")


class Tix(ModuleBuilder):

    @property
    def url(self):
        return f"https://github.com/python/cpython-source-deps/archive/tix-{self.version}.tar.gz"

    @property
    def version(self):
        return "8.4.3.6"

    def xenv_CFLAGS(self):
        # Needed to avoid error: Getting no member named 'result' in 'struct Tcl_Interp'
        yield "-DUSE_INTERP_RESULT"
        yield "-Wno-implicit-function-declaration"  # Allows to not fail compilation due to missing 'panic' symbol
        yield self.checked_deps_folder("include", prefix="-I")

    def xenv_LDFLAGS(self):
        yield f"-L{self.deps_lib}"

    def c_configure_args(self):
        yield "--enable-shared=no"
        yield "--enable-threads"
        yield f"--with-tcl={self.deps_lib}"
        yield f"--with-tk={self.deps_lib}"
        yield "--without-x"

    def _do_linux_compile(self):
        self.run_configure("/bin/sh configure", self.c_configure_args())
        self.run_make()
        self.run_make("install")


class TkInter(ModuleBuilder):
    """Build tcl/tk"""

    m_telltale = None  # ["{include}/tk", "{include}/tk.h"]

    @classmethod
    def candidate_modules(cls):
        return [Tcl, Tk, Tix]

    def auto_use_with_reason(self):
        if not self.target.is_macos and not os.path.isdir("/usr/include/X11"):
            return False, runez.brown("requires libx11-dev")

        return super().auto_use_with_reason()

    @property
    def version(self):
        return "8.6.10"


class Uuid(ModuleBuilder):

    m_telltale = "{include}/uuid/uuid.h"

    def auto_use_with_reason(self):
        if self.target.is_macos:
            return False, runez.blue("on demand on macos")

        if self.target.is_linux:
            path = self._find_telltale(self.m_telltale)
            if path:
                return True, "%s (on top of uuid-dev)" % runez.green("needed on linux")  # pragma: no cover, provisional

            # TODO: fails to link on linux without libsqlite3-dev (works correctly if present)
            return False, runez.red("need uuid-dev on linux as well, pending enhancement")

        return super().auto_use_with_reason()

    @property
    def url(self):
        return f"https://sourceforge.net/projects/libuuid/files/libuuid-{self.version}.tar.gz"

    @property
    def version(self):
        return "1.0.3"

    def xenv_CFLAGS(self):
        yield "-fPIC"

    def _do_linux_compile(self):
        self.run_configure("./configure", "--enable-shared=no", "--enable-static=yes", "--with-pic=yes")
        self.run_make()
        self.run_make("install")


class Xz(ModuleBuilder):

    m_telltale = "{include}/lzma.h"

    @property
    def url(self):
        return f"https://tukaani.org/xz/xz-{self.version}.tar.gz"

    @property
    def version(self):
        return "5.2.5"

    def _do_linux_compile(self):
        self.run_configure(
            "./configure",
            "--enable-shared=no", "--enable-static=yes", "--with-pic=yes",
            "--disable-dependency-tracking", "--disable-doc",
        )
        self.run_make()
        self.run_make("install")


class Zlib(ModuleBuilder):

    m_telltale = "{include}/zlib.h"

    def auto_use_with_reason(self):
        if self.target.is_linux:
            return True, "%s (to get it statically compiled)" % runez.green("needed on linux")

        return super().auto_use_with_reason()

    @property
    def url(self):
        return f"https://zlib.net/zlib-{self.version}.tar.gz"

    @property
    def version(self):
        return "1.2.11"

    def xenv_CFLAGS(self):
        yield "-fPIC"

    def _do_linux_compile(self):
        self.run_configure("./configure", "--64", "--static")
        self.run_make()
        self.run_make("install")
