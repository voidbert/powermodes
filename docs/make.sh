#!/bin/sh

# Regenerate the documentation every time. Makefiles where causing too many troubles, and require
# GNU Make to be installed.

delete_build_source() {
    if [ -d _build ]; then
        rm -r _build
    fi

    if [ -d source ]; then
        rm -r source
    fi
}

help_message() {
    echo "Usage:"
    echo "./make.sh clean           - remove build residues"
    echo "./make.sh build           - build documentation"
    echo "./make.sh build --private - build documentation with private methods (powermodes developers)"
}

if [ "$1" = "clean" ]; then

    if [ $# -eq 1 ]; then
        delete_build_source
    else
        help_message
    fi

elif [ "$1" = "build" ]; then

    if [ $# -eq 2 ]; then

        if [ "$2" = "--private" ]; then
            private=--private
        else
            help_message
            exit 0
        fi

    elif [ $# -ne 1 ]; then
        help_message
        exit 0
    fi

    delete_build_source

    sphinx-apidoc --no-headings $private -e -o source ../powermodes
    sphinx-build . _build
else
    help_message
fi
