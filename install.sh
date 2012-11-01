#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function printUsage {
    echo "Usage:"
    echo "   install.sh install| uninstall | reinstall | depcheck [install_path]"
}

# Args 3 and 4 are passed through reference:
# $1 - import name; $2 - module nape (installed through e.g. apt, Pacman, etc.)
# $3 - ${DEPRET}, $4 - ${DEPNEED} to update
function check_python_modules {
    if [[ ${1} && ${2} && ${3} ]]; then
        if [[ ! -e subconvertpycheck.py ]]; then
            touch subconvertpycheck.py
        fi

        echo "import ${1}" > subconvertpycheck.py
        python subconvertpycheck.py 2> /dev/null

        if [[ $? -ne 0 ]]; then
            echo "[ERR] ${1} not found."
            DEPRET=1
            DEPNEED=$(echo ${4} ${2})
        else
            echo "[INF] ${1} found."
        fi

        rm -f subconvertpycheck.py
    else
        echo "[!!!] Incorrect arguments in check_python_modules! This is installer bug and should be reported!"
        echo "[!!!] Debug output: ${1} ;; ${2} ;; ${3} ;; ${4}"
        exit 1
    fi
}

# Args:
# command, printable name, error level, ${DEPRET}, ${DEPNEED}
function check_software {
    if [[ ${1} && ${2} && ${3} && ${4} ]]; then
        ${1} > /dev/null 2>&1
        if [[ $? -ne 0 ]]; then
            echo "${3} ${2} not found."
            if [[ ${3} == "[ERR]" ]]; then
                DEPRET=1
            fi
            DEPNAME=$(echo ${1} | sed "s/ .*//")
            DEPNEED="${5} ${DEPNAME}"
        else
            echo "[INF] ${2} found."
        fi
    else
        echo "[!!!] Incorrect arguments in check_software! This is installer bug and should be reported!"
        echo "[!!!] Debug output: ${1} ;; ${2} ;; ${3} ;; ${4} ;; ${5}"
        exit 1
    fi

}

function check_dependencies {
    # dependencies: python2.6, python-qt4, python-chardet, mplayer, gettext
    DEPRET=0
    DEPNEED=""

    PYTHON_VERSION=$(python --version 2>&1 | sed "s/Python //") # Might be 2.7.2+
    PYTHON_BIG_VERSION=$(echo ${PYTHON_VERSION} | grep -o "^[0-9]\+.[0-9]\+" | sed "s/\.//")

    # Check Python version
    if [[ PYTHON_BIG_VERSION -lt 26 ]]; then
        echo "[ERR] Python version: ${PYTHON_VERSION}. Required: >2.6"
        DEPRET=1
        DEPNEED="${DEPNEED} python2.6"
    else
        echo "[INF] Python version: ${PYTHON_VERSION}."
    fi


    # Python libs
    check_python_modules "PyQt4" "python-qt4" ${DEPRET} ${DEPNEED}
    check_python_modules "chardet" "python-chardet" ${DEPRET} ${DEPNEED}

    # Software
    check_software "gettext --version" "gettext" "[WRN]" ${DEPRET} ${DEPNEED}
    # mplayer -v is not a proper mplayer switch but it doesn't produce an error
    check_software "mplayer -v" "MPlayer" "[ERR]" ${DEPRET} ${DEPNEED}


    if [[ ${DEPNEED} != "" ]]; then
        echo -ne "------------------------------\nNot all dependencies are installed on the system. "
        if [[ ${DEPRET} -eq 0 ]]; then
            echo -n "Note that some of them are not required (see manual for reference). "
        fi
        echo -e "You might consider copying the following list of not installed packages to your package manager:\n"
        echo -e "    ${DEPNEED}\n------------------------------"
    fi

    return ${DEPRET}
}

function remove {
    if [[ -e "${1}" ]]; then
        if [[ $# -eq 2 && ${2} == "dir" ]]; then
            echo "[INF] Removing directory ${1}..."
            rm -rf "${1}"
        else
            echo "[INF] Removing file ${1}..."
            rm -f "${1}"
        fi
    else
        echo "[WRN] ${1} doesn't exist!"
    fi
}

function getPath {
    # ${1} provides a "prompt" text in this function
    if [[ $# -eq 0 ]]; then
        echo "[ERR] I cowardly refuse to do nothing..."
        exit 1
    else
        DEFAULT_DIR=/usr
        if [[ "${INSTALL_DIR}" == "" ]]; then
            echo "${1} [Default (press enter to use): ${DEFAULT_DIR}]:"
            echo -n "> "
            read INSTALL_DIR
        fi
        if [[ "${INSTALL_DIR}" == "" ]]; then
            INSTALL_DIR=${DEFAULT_DIR}
        else
            INSTALL_DIR="${INSTALL_DIR}"
        fi

        SUBC_BIN="${INSTALL_DIR}/bin"
        SUBC_SHARE="${INSTALL_DIR}/share/subconvert"
        SUBC_LOCALE="${INSTALL_DIR}/share/locale"
        SUBC_DOC="${INSTALL_DIR}/share/doc/subconvert"
    fi
}

function installLocales {
    for LDIR in ${DIR}/subconvert/locale/*; do
        POFILE="${LDIR}/LC_MESSAGES/subconvert.po"
        MOFILE="${LDIR}/LC_MESSAGES/subconvert.mo"
        if [[ -e ${POFILE} ]]; then
            if [[ -e ${MOFILE} ]]; then
                echo "[INF] Removing existing ${MOFILE}"
                rm -f ${MOFILE}
            fi
            msgfmt ${POFILE} -o ${MOFILE}
            MODEST="${SUBC_LOCALE}/$(basename ${LDIR})/LC_MESSAGES/"
            cp ${MOFILE} ${MODEST} 2> /dev/null
            if [[ $? -ne 0 ]]; then
                mkdir -p ${MODEST}
                cp ${MOFILE} ${MODEST}
            fi
        fi
    done
}

function installSubConvert {
    if [[ ! -e ${INSTALL_DIR} ]]; then
        echo -e "[ERR] It seems that '${INSTALL_DIR}' doesn't exist. Keep in mind that you have to provide path to existing directory in which a 'subconvert' directory can be created. Frequent choices are user HOME directory or '/usr' directory."
        echo "Please try to run the install script again."
        exit 1
    fi

    if [[ -e ${SUBC_SHARE} || -e ${SUBC_DOC} || -e ${SUBC_BIN}/subconvert || -e ${SUBC_BIN}/subconvert-gui ]]
    then
        echo "[ERR] It seems that previous version of SubConvert wasn't properly removed. Please try to uninstall it first."
        exit 1
    fi

    echo "[INF] Dependencies:"
    check_dependencies
    if [[ $? -ne 0 ]]; then
        echo "[ERR] Required packages are not installed."
        exit 1
    else
        echo "[INF] Dependency check passed."
    fi

    mkdir -p ${SUBC_SHARE}/subconvert
    if [[ $? -gt 0 ]]; then
        echo "[ERR] Cannot create ${SUBC_SHARE} directory. Do you have proper permissions?"
        exit 1
    fi

    echo "[INF] Copying files to ${SUBC_SHARE}"
    cp ${DIR}/{subconvert.py,subconvert-gui.py,install.sh} ${SUBC_SHARE} || exit 1
    cp ${DIR}/subconvert/*.py ${SUBC_SHARE}/subconvert
    cp -r ${DIR}/subconvert/subparser ${SUBC_SHARE}/subconvert
    cp -r ${DIR}/subconvert/subutils ${SUBC_SHARE}/subconvert
    cp -r ${DIR}/subconvert/img ${SUBC_SHARE}/subconvert
    chmod +x ${SUBC_SHARE}/{subconvert.py,subconvert-gui.py,install.sh}
    echo "[INF] Copying files to ${SUBC_DOC}..."
    if [[ ! -e ${SUBC_DOC} ]]; then
        echo "[INF] ${SUBC_DOC} doesn't exist. Creating it."
        mkdir -p ${SUBC_DOC}
    fi
    if [[ -d ${SUBC_DOC} ]]; then
        cp ${DIR}/{CHANGELOG,LICENSE.txt,README} ${SUBC_DOC}
    else
        echo "[WRN] ${SUBC_DOC} is not a directory! Skipping doc files!"
    fi
    echo "[INF] Creating symbolic links..."
    if [[ ! -e ${SUBC_BIN} ]]; then
        echo "[INF] ${SUBC_BIN} doesn't exist. Creating it."
        mkdir -p ${SUBC_BIN}
    fi
    ln -s ${SUBC_SHARE}/subconvert.py ${SUBC_BIN}/subconvert
    ln -s ${SUBC_SHARE}/subconvert-gui.py ${SUBC_BIN}/subconvert-gui

    if [[ ! -e ${INSTALL_DIR}/share/applications ]]; then
        echo "[INF] ${INSTALL_DIR}/share/applications doesn't exist. Creating it."
        mkdir -p ${INSTALL_DIR}/share/applications
    fi
    cp ${DIR}/subconvert.desktop ${INSTALL_DIR}/share/applications

    if [[ ! -e ${INSTALL_DIR}/share/icons/hicolor ]]; then
        echo "[WRN] ${INSTALL_DIR}/share/icons/hicolor doesn't exist."
        mkdir -p ${INSTALL_DIR}/share/icons/hicolor/{128x128,16x16,192x192,22x22,24x24,256x256,32x32,36x36,48x48,64x64,72x72,96x96,scalable}

        echo "[INF] Downloading hicolor theme."
        wget http://www.freedesktop.org/software/icon-theme/releases/hicolor-icon-theme-0.5.tar.gz
        if [[ $? -ne 0 ]]; then
            echo "[ERR] Installation of hicolor theme unsuccessfull! Stopping installation."
            exit 1
        fi

        echo "[INF] Installing hicolor theme."
        mkdir -p ${DIR}/hicolor_install
        mv hicolor-icon-theme-0.5.tar.gz ${DIR}/hicolor_install
        pushd .
        cd ${DIR}/hicolor_install
        tar -xzf hicolor-icon-theme-0.5.tar.gz
        cd hicolor-icon-theme-0.5
        cp index.theme ${INSTALL_DIR}/share/icons/hicolor/

        popd
        rm -rf ${DIR}/hicolor_install
    fi
    cp -r ${DIR}/subconvert/img/icons/* ${INSTALL_DIR}/share/icons/hicolor/

    if [[ ! -e ${INSTALL_DIR}/share/pixmaps ]]; then
        echo "[INF] ${INSTALL_DIR}/share/pixmaps doesn't exist. Creating it."
        mkdir -p ${INSTALL_DIR}/share/pixmaps
    fi
    ln -s ${INSTALL_DIR}/share/icons/hicolor/scalable/subconvert.svg ${INSTALL_DIR}/share/pixmaps/subconvert.svg
    ln -s ${INSTALL_DIR}/share/icons/hicolor/48x48/subconvert.png ${INSTALL_DIR}/share/pixmaps/subconvert-48.png
    ln -s ${INSTALL_DIR}/share/icons/hicolor/32x32/subconvert.png ${INSTALL_DIR}/share/pixmaps/subconvert-32.png

    echo "[INF] Creating and copying locales..."
    installLocales
    echo "Installation finished succesfully!"
}

function uninstallSubConvert {
    remove ${SUBC_BIN}/subconvert
    remove ${SUBC_BIN}/subconvert-gui
    remove ${SUBC_SHARE} "dir"
    remove ${SUBC_DOC} "dir"
    remove ${INSTALL_DIR}/share/pixmaps/subconvert.svg
    remove ${INSTALL_DIR}/share/pixmaps/subconvert-48.png
    remove ${INSTALL_DIR}/share/pixmaps/subconvert-32.png

    for SIZE in ${INSTALL_DIR}/share/icons/hicolor/*;
    do
        if [[ -d ${SIZE} && -e ${SIZE}/subconvert.png ]]; then
            remove ${SIZE}/subconvert.png
        elif [[ -d ${SIZE} && -e ${SIZE}/subconvert.svg ]]; then
            remove ${SIZE}/subconvert.svg
        fi
    done

    for LANG in ${INSTALL_DIR}/share/locale/*;
    do
        if [[ -d ${LANG} && -e ${LANG}/LC_MESSAGES/subconvert.mo ]]; then
            remove ${LANG}/LC_MESSAGES/subconvert.mo
        fi
    done
}

# Execution starts here

if [[ $# -lt 1 && $# -gt 2 ]]; then
    echo "Incorrect call of install script!"
    printUsage
    exit 1
fi

ACTION=${1}
INSTALL_DIR=${2}

case ${ACTION} in
    install)
        getPath "Select directory to install SubConvert"
        installSubConvert
        ;;
    uninstall)
        getPath "Select SubConvert PREFIX directory"
        uninstallSubConvert
        ;;
    reinstall)
        getPath "Reinstallation: Select SubConvert PREFIX directory"
        echo -e "\nTrying to uninstall..."
        uninstallSubConvert
        echo -e "\nInstalling new SubConvert..."
        installSubConvert
        ;;
    depcheck)
        echo "Scanning dependencies..."
        check_dependencies
        exit $?
        ;;
    *)
        echo "Incorrect call of install script!"
        printUsage
        exit 1
        ;;
esac

