#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function printUsage {
    echo "Usage:"
    echo "   install.sh install | uninstall | reinstall"
}

function remove {
    if [[ -e "${1}" ]]; then
        if [[ $# -eq 2 && ${2} == "dir" ]]; then
            echo "Removing directory ${1}..."
            rm -rf "${1}"
        else
            echo "Removing file ${1}..."
            rm -f "${1}"
        fi
    else
        echo "ERROR: ${1} doesn't exist!"
    fi
}

function getPath {
    # ${1} provides a "prompt" text in this function
    if [[ $# -eq 0 ]]; then
        echo "I cowardly refuse to do nothing..."
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
                echo Removing existing ${MOFILE}
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
        echo -e "ERROR: It seems that '${INSTALL_DIR}' doesn't exist. Keep in mind that you have to provide path to existing directory in which a 'subconvert' directory can be created. Frequent choices are user HOME directory or '/usr' directory."
        echo "Please try to run the install script again."
        exit 1
    fi

    if [[ -e ${SUBC_SHARE} || -e ${SUBC_DOC} || -e ${SUBC_BIN}/subconvert || -e ${SUBC_BIN}/subconvert-gui ]]
    then
        echo "It seems that previous version of SubConvert wasn't properly removed. Please try to uninstall it first."
        exit 1
    fi

    mkdir -p ${SUBC_SHARE}/subconvert
    if [[ $? -gt 0 ]]; then
        echo "ERROR: Cannot create ${SUBC_SHARE} directory. Do you have proper permissions?"
        exit 1
    fi

    echo "Copying files to ${SUBC_SHARE}"
    cp ${DIR}/{subconvert.py,subconvert-gui.py,install.sh} ${SUBC_SHARE} || exit 1
    cp ${DIR}/subconvert/*.py ${SUBC_SHARE}/subconvert
    cp -r ${DIR}/subconvert/subparser ${SUBC_SHARE}/subconvert
    chmod +x ${SUBC_SHARE}/{subconvert.py,subconvert-gui.py,install.sh}
    echo "Copying files to ${SUBC_DOC}..."
    if [[ ! -e ${SUBC_DOC} ]]; then
        echo "${SUBC_DOC} doesn't exist. Creating it."
        mkdir -p ${SUBC_DOC}
    fi
    if [[ -d ${SUBC_DOC} ]]; then
        cp ${DIR}/{CHANGELOG,LICENSE.txt,README} ${SUBC_DOC}
    else
        echo "WARNING! ${SUBC_DOC} is not a directory! Skipping doc files!"
    fi
    echo "Creating symbolic links..."
    if [[ ! -e ${SUBC_BIN} ]]; then
        echo "${SUBC_BIN} doesn't exist. Creating it."
        mkdir -p ${SUBC_BIN}
    fi
    ln -s ${SUBC_SHARE}/subconvert.py ${SUBC_BIN}/subconvert
    ln -s ${SUBC_SHARE}/subconvert-gui.py ${SUBC_BIN}/subconvert-gui
    echo "Creating and copying locales..."
    installLocales
    echo "Installation finished succesfully!"

}

function uninstallSubConvert {
    remove ${SUBC_BIN}/subconvert
    remove ${SUBC_BIN}/subconvert-gui
    remove ${SUBC_SHARE} "dir"
    remove ${SUBC_DOC} "dir"

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
    *)
        echo "Incorrect call of install script!"
        printUsage
        exit 1
        ;;
esac

