# PSP EBOOT Signer

`ebootsign` is a host-side utility for converting an unsigned PSP
`EBOOT.PBP` into a signed `EBOOT.PBP`.

The code originated as a GNU/Linux port of PSCRYPTER by Carlosgs and was
adapted to avoid loading an entire EBOOT into one static input buffer.

## Build

This is a normal host CMake project. It does not use the PSP cross compiler and
does not invoke `psp-config`.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
```

The build is compiled warning-clean with current GCC and Clang using
`-Wall -Wextra -Werror`, with unused API parameters explicitly excluded from
that policy.

## Test

The test suite generates a minimal deterministic unsigned PBP containing a
valid PSP PRX ELF header, signs it twice with the built executable, validates
the resulting PBP and `~PSP` structure, and verifies that both signed outputs
are byte-identical.

```sh
ctest --test-dir build --output-on-failure
```

No binary EBOOT fixture is stored in the repository.

## Install

Installation follows standard CMake prefix semantics:

```sh
cmake --install build --prefix /desired/prefix
```

For PSPDEV integration, the caller can choose `$PSPDEV` as the prefix:

```sh
cmake --install build --prefix "$PSPDEV"
```

The project performs no privilege detection or elevation. Permission policy
belongs to the caller or the enclosing PSPDEV installer.

## Usage

```sh
ebootsign EBOOT.PBP EBOOT_signed.PBP
```

For a Make-based homebrew project, a signing rule can be written as:

```make
EBOOT_signed.PBP: EBOOT.PBP
	ebootsign $< $@
```
