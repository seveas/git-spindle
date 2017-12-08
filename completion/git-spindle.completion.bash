#!/bin/bash

# Set this to yes in your environment to enable completions that require API
# calls and will be slower.
GIT_SPINDLE_COMPLETE_REMOTE=${GIT_SPINDLE_COMPLETE_REMOTE-no}

_git_hub() {
    local subcommands="
        add-account
        add-collaborator
        add-deploy-key
        add-hook
        add-public-keys
        add-remote
        apply-pr
        browse
        calendar
        cat
        check-pages
        clone
        collaborators
        config
        create
        create-token
        deploy-keys
        edit-hook
        fetch
        fork
        forks
        gist
        gists
        hooks
        ignore
        ip-addresses
        issue
        issues
        log
        ls
        mirror
        network
        public-keys
        pull-request
        remove-collaborator
        remove-deploy-key
        remove-hook
        render
        repos
        say
        set-origin
        status
        whoami
        whois
"

    local subcommand="$(__git_find_on_cmdline "$subcommands")"
    if [ -z "$subcommand" ]; then
        case "${cur}" in
            --account=*)
                __gitcomp "$(sed -ne 's/\[github "\(.*\)"]/\1/p' ~/.gitspindle)" "" "${cur##--account=}"
                ;;
            --*)
                __gitcomp "--account="
                ;;
            *)
                __gitcomp "$subcommands"
                ;;
        esac
        return
    fi

    local completion_func="_git_spindle_${subcommand//-/_}"
    declare -f $completion_func >/dev/null && $completion_func hub
    # Default to no completion, subcommands that expect filenames call _filedir
    # explicitly.
    compopt +o default
}

_git_lab() {
    local subcommands="
        add-account
        add-public_keys
        add-member
        add-remote
        apply-merge
        browse
        calendar
        config
        cat
        clone
        create
        fetch
        fork
        issue
        issues
        log
        ls
        members
        merge-request
        mirror
        protect
        protected
        public-keys
        remove-member
        repos
        set-origin
        unprotect
        whoami
        whois
"

    local subcommand="$(__git_find_on_cmdline "$subcommands")"
    if [ -z "$subcommand" ]; then
        case "${cur}" in
            --account=*)
                __gitcomp "$(sed -ne 's/\[gitlab "\(.*\)"]/\1/p' ~/.gitspindle)" "" "${cur##--account=}"
                ;;
            --*)
                __gitcomp "--account="
                ;;
            *)
                __gitcomp "$subcommands"
                ;;
        esac
        return
    fi

    local completion_func="_git_spindle_${subcommand//-/_}"
    declare -f $completion_func >/dev/null && $completion_func lab
    # Default to no completion, subcommands that expect filenames call _filedir
    # explicitly.
    compopt +o default
}

_git_bb() {
    local subcommands="
        add-account
        add-deploy_key
        add-privilege
        add-public_keys
        add-remote
        browse
        cat
        clone
        config
        create
        deploy-keys
        fetch
        fork
        forks
        invite
        issue
        issues
        ls
        mirror
        privileges
        public-keys
        pull-request
        remove-deploy-key
        remove-privilege
        repos
        set-origin
        snippet
        snippets
        whoami
        whois
"

    local subcommand="$(__git_find_on_cmdline "$subcommands")"
    if [ -z "$subcommand" ]; then
        case "${cur}" in
            --account=*)
                __gitcomp "$(sed -ne 's/\[bitbucket "\(.*\)"]/\1/p' ~/.gitspindle)" "" "${cur##--account=}"
                ;;
            --*)
                __gitcomp "--account="
                ;;
            *)
                __gitcomp "$subcommands"
                ;;
        esac
        return
    fi

    local completion_func="_git_spindle_${subcommand//-/_}"
    declare -f $completion_func >/dev/null && $completion_func bb
    # Default to no completion, subcommands that expect filenames call _filedir
    # explicitly.
    compopt +o default
}

_git_bucket() {
    _git_bb "$@"
}

##########################################################################

_git_spindle_add_account() {
    case "$1,${cur}" in
        hub,--*|lab,--*)
            __gitcomp "--host="
            ;;
    esac
}

_git_spindle_add_deploy_key() {
    case "$1,${cur}" in
        hub,--*)
            __gitcomp "--read-only"
            return
            ;;
    esac
    _filedir "@(pub)"
}

_git_spindle_add_member() {
    case "$cur" in
        --access-level=*)
            __gitcomp "guest reporter developer master owner" "" "${cur##--access-level=}"
            ;;
        --*)
            __gitcomp "--access-level="
            ;;
    esac
}

_git_spindle_add_privilege() {
    __git_spindle_options "--admin --read --write"
}

_git_spindle_add_public_keys() {
    _filedir "@(pub)"
}

_git_spindle_add_remote() {
    __git_spindle_protocols $1
    __git_spindle_forks $1
}

declare -A __git_spindle_browse_sections
__git_spindle_browse_sections[hub]="
    issues
    pulls
    wiki
    branches
    releases
    contributors
    graphs
    settings
"
__git_spindle_browse_sections[lab]="
    issues
    merge_requests
    wiki
    files
    commits
    branches
    graphs
    settings
"
__git_spindle_browse_sections[bb]="
    src
    commits
    branches
    pull-requests
    downloads
    admin
    issues
    wiki
"
_git_spindle_browse() {
    __git_spindle_options "--parent" && return
    __gitcomp "${__git_spindle_browse_sections[$1]}"
    __git_spindle_repos $1
}

_git_spindle_cat() {
    _filedir
}

_git_spindle_clone() {
    __git_spindle_protocols $1
    __git_spindle_options "
                --parent
                --local
                --no-hardlinks
                --shared
                --reference
                --quiet
                --no-checkout
                --bare
                --mirror
                --origin
                --upload-pack
                --template=
                --depth
                --single-branch
                --branch
                --triangular
                --upstream-branch=
            " append
}

_git_spindle_config() {
    __git_spindle_options "--unset" && return
    case $1 in
        bb)
            __gitcomp "user password"
            ;;
        hub)
            __gitcomp "user token auth-id host"
            ;;
        lab)
            __gitcomp "user token host"
            ;;
    esac
}

_git_spindle_create() {
    if [ $1 = lab ]; then
        __git_spindle_options "--private --internal --description="
    else
        __git_spindle_options "--private --description="
    fi
}

_git_spindle_create_token() {
    __git_spindle_options "--store"
}

_git_spindle_fetch() {
    __git_spindle_protocols $1
    __git_spindle_forks $1
}

_git_spindle_fork() {
    _git_spindle_set_origin $1
}

_git_spindle_gist() {
    __git_spindle_options "--description=" && return
    _filedir
}

_git_spindle_ignore() {
    test "$GIT_SPINDLE_COMPLETE_REMOTE" = no && return
    __gitcomp_nl "$(git hub ignore | sed -ne 's/^ *\* *//p')"
}

_git_spindle_invite() {
    __git_spindle_options "--admin --read --write"
}

_git_spindle_ip_addresses() {
    __git_spindle_options "--git --hooks --importer --pages"
}

_git_spindle_issue() {
    __git_spindle_options "--parent"
}

_git_spindle_issues() {
    __git_spindle_options "--parent"
}

_git_spindle_log() {
    __git_spindle_options "--type= --count= --verbose"
    # TODO actually complete the types
}

_git_spindle_ls() {
    _filedir
}

_git_spindle_mirror() {
    __git_spindle_protocols $1
    __git_spindle_options "--goblet" append
}

_git_spindle_protect() {
    __gitcomp_nl "$(__git_heads)"
}

_git_spindle_pull_request() {
    if [ $1 = hub ]; then
        __git_spindle_options "--issue="
    fi
}

_git_spindle_remove_collaborator() {
    test "$GIT_SPINDLE_COMPLETE_REMOTE" = no && return
    __gitcomp "$(git hub collaborators)"
}

_git_spindle_remove_member() {
    test "$GIT_SPINDLE_COMPLETE_REMOTE" = no && return
    __gitcomp "$(git lab members | awk '{print $2}')"
}

_git_spindle_remove_privilege() {
    test "$GIT_SPINDLE_COMPLETE_REMOTE" = no && return
    __gitcomp "$(git bb privileges | awk '{print $2}')"
}

_git_spindle_render() {
    _filedir '@(md|rst)'
}

_git_spindle_repos() {
    __git_spindle_options "--no-forks"
}

_git_spindle_snippet() {
    __git_spindle_options "--description=" && return
    _filedir
}

_git_spindle_set_origin() {
    __git_spindle_protocols $1
    __git_spindle_options "--triangular --upstream-branch=" append
}

_git_spindle_unprotect() {
    __gitcomp_nl "$(__git_heads)"
}

##########################################################################

__git_spindle_protocols() {
    case $1,$cur in
        hub,--*)
            __gitcomp "--http --ssh --git"
            ;;
        *,--*)
            __gitcomp "--http --ssh"
            ;;
    esac
}
__git_spindle_forks() {
    case "$1,$GIT_SPINDLE_COMPLETE_REMOTE,$cur" in
        *,no,*|lab,*|*,--*)
            ;;
        *)
            __gitcomp_nl_append "$(git $1 forks 2>/dev/null | sed -e 's/\[\(.*\)\].*/\1/')"
            ;;
    esac
}

__git_spindle_repos() {
    case "$GIT_SPINDLE_COMPLETE_REMOTE,$cur" in
        no,*|*,--*)
            ;;
        *)
            __gitcomp_nl_append "$(git $1 repos | sed -e 's/ .*//')"
            ;;
    esac
}

__git_spindle_options() {
    case "$2,$cur" in
        append,--*)
            __gitcompappend "$1" "" "$cur" " "
            return
            ;;
        *,--*)
            __gitcomp "$1"
            return
            ;;
    esac
    return 1
}
