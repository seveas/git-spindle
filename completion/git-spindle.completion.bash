#!/bin/bash

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
        help
        hooks
        ignore
        ip-addresses
        issue
        issues
        log
        ls
        mirror
        network
        protect
        protected
        public-keys
        pull-request
        readme
        release
        releases
        remove-collaborator
        remove-deploy-key
        remove-hook
        render
        repos
        say
        set-origin
        setup-goblet
        status
        unprotect
        whoami
        whois
    "
    local sections="
        branches
        contributors
        graphs
        issues
        pulls
        releases
        settings
        wiki
    "
    __git_spindle hub github
}

_git_lab() {
    local subcommands="
        add-account
        add-member
        add-public-keys
        add-remote
        apply-merge
        browse
        calendar
        cat
        clone
        config
        create
        fetch
        fork
        help
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
    local sections="
        branches
        commits
        files
        graphs
        issues
        merge_requests
        settings
        wiki
    "
    __git_spindle lab gitlab
}

_git_bb() {
    local subcommands="
        add-account
        add-deploy-key
        add-privilege
        add-public-keys
        add-remote
        apply-pr
        browse
        cat
        clone
        config
        create
        deploy-keys
        fetch
        fork
        forks
        help
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
    local sections="
        admin
        branches
        commits
        downloads
        issues
        pull-requests
        src
        wiki
    "
    __git_spindle bb bitbucket
}

_git_bucket() {
    _git_bb
}

__git_spindle() {
    # Default to no completion, subcommands that expect filenames call _filedir
    # explicitly.
    [ "$(type -t compopt)" = builtin ] && compopt +o default

    # Do nothing if bash-completion version is too old
    ( declare -p words && declare -p cword ) >/dev/null 2>&1 || return

    _split_longopt

    local subcommand="$(__git_find_on_cmdline "$subcommands")"

    local -a previous_args
    local -a valued_options=(
        --host
        --access-level
        --upstream-branch
        --team
        --description
        --org
        --group
        --type
        --count
        --enforcement-level
        --contexts
        --issue
        --save
        # valued git clone options
        --reference
        --reference-if-able
        --origin
        --branch
        --upload-pack
        --template
        --config
        --depth
        --separate-git-dir
        --jobs
        --shallow-since
        --shallow-exclude
    )
    __git_spindle_set_previous_args previous_args valued_options
    [ "${previous_args[0]}" = "$subcommand" ] || subcommand=

    case "$prev,$cur" in
        --account,*)
            if [ -n "$subcommand" -o ${#previous_args[@]} -eq 0 ]; then
                local -a line
                while read -a line; do
                    [ ${line[0]} = "[$2" ] && __gitcompappend "${line[1]:1:${#line[1]}-3}" "" "$cur" " "
                done <~/.gitspindle
                return
            fi
            ;;
        *,--*)
            if [ -n "$subcommand" -o ${#previous_args[@]} -eq 0 ]; then
                __git_spindle_options "--account=" no_space
            fi
            ;;
        *)
            if [ -z "$subcommand" -a ${#previous_args[@]} -eq 0 ]; then
                __gitcomp "$subcommands"
                return
            fi
            ;;
    esac

    local completion_func="_git_spindle_${subcommand//-/_}"
    local -f $completion_func >/dev/null && $completion_func $1
}

##########################################################################

_git_spindle_add_account() {
    case "$1" in
        hub|lab)
            case "$prev" in
                --host)
                    unset COMPREPLY
                    ;;
                *)
                    __git_spindle_options "--host=" no_space
                    ;;
            esac
            ;;
    esac
}

_git_spindle_add_collaborator() {
    __git_spindle_options || __git_spindle_forks $1
}

_git_spindle_add_deploy_key() {
    case "$1" in
        hub)
            __git_spindle_options "--read-only" && return
            ;;
    esac
    __git_spindle_options || _filedir "@(pub)"
}

_git_spindle_add_hook() {
    __git_spindle_options && return

    case ${#previous_args[@]} in
        1)
            __gitcomp "web"

            [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

            local IFS=$'\n\r'
            local -a hooks=($(DEBUG=1 git hub available-hooks 2>/dev/null))
            __gitcomp_nl_append "${hooks[*]}"
            ;;
        *)
            __git_spindle_hook_settings
            ;;
    esac
}

_git_spindle_add_member() {
    case "$prev" in
        --access-level)
            unset COMPREPLY
            __gitcomp "guest reporter developer master owner"
            ;;
        *)
            __git_spindle_options "--access-level=" no_space
            ;;
    esac
}

_git_spindle_add_privilege() {
    __git_spindle_options "--admin --read --write" && return

    __git_spindle_forks $1
}

_git_spindle_add_public_keys() {
    __git_spindle_options || _filedir "@(pub)"
}

_git_spindle_add_remote() {
    __git_spindle_protocols $1 && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_forks $1
}

_git_spindle_apply_merge() {
    __git_spindle_options && return
    [ ${#previous_args[@]} -eq 1 ] || return

    local -a merge_refs=($(git for-each-ref --format '%(refname:strip=2)' refs/merge-requests/ --no-merged))
    __gitcomp "${merge_refs[*]/%\/head}"
}

_git_spindle_apply_pr() {
    __git_spindle_options && return
    [ ${#previous_args[@]} -eq 1 ] || return

    case "$1,${GIT_SPINDLE_COMPLETE_REMOTE-no}" in
        hub,*)
            local -a pull_refs=($(git for-each-ref --format '%(refname:strip=2)' refs/pull/ --no-merged))
            __gitcomp "${pull_refs[*]/%\/head}"
            ;;
        bb,no)
            ;;
        bb,*)
            local IFS=$'\n'
            local -a issues=($(git bb issues 2>/dev/null))
            issues=("${issues[@]##Issues *}")
            issues=("${issues[@]##Pull *}")
            issues=("${issues[@]##*/issues/*}")
            issues=("${issues[@]#[}")
            __gitcomp_nl_append "${issues[*]%%]*}"
            ;;
    esac
}

_git_spindle_browse() {
    __git_spindle_options "--parent" && return

    case ${#previous_args[@]} in
        1)
            __git_spindle_repos $1
            ;;
        2)
            __gitcomp "$sections"
            ;;
    esac
}

_git_spindle_cat() {
    __git_spindle_options || _filedir
}

_git_spindle_check_pages() {
    __git_spindle_options "--parent" && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_clone() {
    case "$prev" in
        --reference|--reference-if-able|--origin|--branch|--upload-pack|--template|--config|--depth|--separate-git-dir|--jobs|--shallow-since|--shallow-exclude)
            unset COMPREPLY
            ;;
        *)
            __git_spindle_set_origin $1 || return

            __git_spindle_options "--parent"
            # Git clone options as of Git 2.11.0
            if [ ${#previous_args[@]} -eq 1 ]; then
                __git_spindle_options "
                            --quiet
                            --verbose
                            --no-checkout
                            --bare
                            --mirror
                            --progress
                            --single-branch
                            --no-single-branch
                            --recursive
                            --recurse-submodules
                            --local
                            --no-hardlinks
                            --shared
                            --dissociate
                            --shallow-submodules
                            --no-shallow-submodules
                            --ipv4
                            --ipv6
                        "
                __git_spindle_options "
                            --reference=
                            --reference-if-able=
                            --origin=
                            --branch=
                            --upload-pack=
                            --template=
                            --config=
                            --depth=
                            --separate-git-dir=
                            --jobs=
                            --shallow-since=
                            --shallow-exclude=
                        " no_space
            fi

            __git_spindle_options && return

            case ${#previous_args[@]} in
                1)
                    __git_spindle_repos $1
                    ;;
                2)
                    _filedir -d
                    ;;
            esac
            ;;
    esac
}

_git_spindle_collaborators() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_config() {
    __git_spindle_options "--unset" && return

    [ ${#previous_args[@]} -eq 1 ] || return

    case "$1" in
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
    case "$1,$prev" in
        *,--description|bb,--team|lab,--group)
            unset COMPREPLY
            ;;
        hub,--org)
            unset COMPREPLY

            [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

            local IFS=$' ,\r'
            local -a line
            while read -a line; do
                if [ "${line[*]:0:2}" = "Member of" ]; then
                    __gitcomp "${line[*]:2}"
                    return
                fi
            done < <(git hub whoami 2>/dev/null)
            ;;
        *)
            __git_spindle_options "--private"
            __git_spindle_options "--description=" no_space

            case "$1" in
                bb)
                    __git_spindle_options "--team=" no_space
                    ;;
                hub)
                    __git_spindle_options "--org=" no_space
                    ;;
                lab)
                    __git_spindle_options "--internal"
                    __git_spindle_options "--group=" no_space
                    ;;
            esac
            ;;
    esac
}

_git_spindle_create_token() {
    __git_spindle_options "--store"
}

_git_spindle_deploy_keys() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_edit_hook() {
    __git_spindle_options && return

    case ${#previous_args[@]} in
        1)
            __git_spindle_hooks
            ;;
        *)
            __git_spindle_hook_settings "-*"
            ;;
    esac
}

_git_spindle_fetch() {
    __git_spindle_protocols $1 && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_forks $1
}

_git_spindle_fork() {
    __git_spindle_set_origin $1 || return
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1 no_own
}

_git_spindle_forks() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_gist() {
    case "$prev" in
        --description)
            unset COMPREPLY
            ;;
        *)
            __git_spindle_options "--description=" no_space && return
            _filedir
            ;;
    esac
}

_git_spindle_help() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __gitcomp "$subcommands"
}

_git_spindle_ignore() {
    __git_spindle_options && return

    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n\r'
    local -a ignore_languages=($(git hub ignore))
    ignore_languages=("${ignore_languages[@]##Languages *}")
    __gitcomp_nl "${ignore_languages[*]#  \* }"

    declare -p COMPREPLY
}

_git_spindle_invite() {
    __git_spindle_options "--admin --read --write"
}

_git_spindle_ip_addresses() {
    __git_spindle_options "--git --hooks --importer --pages"
}

_git_spindle_issue() {
    __git_spindle_options "--parent" && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1

    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return
    printf "%d" "$cur" &>/dev/null || return

    local repo
    printf "%d" "${previous_args[1]}" &>/dev/null || repo="${previous_args[1]}"

    local IFS=$'\n\r'
    local -a issues=($(git $1 issues $repo 2>/dev/null))
    issues=("${issues[@]##Issues *}")
    issues=("${issues[@]##Merge *}")
    issues=("${issues[@]##Pull *}")
    issues=("${issues[@]#[}")
    __gitcomp_nl_append "${issues[*]%%]*}"
}

_git_spindle_issues() {
    __git_spindle_options "--parent" && return

    case $1,${#previous_args[@]} in
        *,1)
            __git_spindle_repos $1
            ;;
        hub,*)
            case "$cur" in
                milestone=*)
                    __gitcomp "'*' none" "" "${cur#milestone=}"
                    ;;
                state=*)
                    __gitcomp "all open closed" "" "${cur#state=}"
                    ;;
                assignee=*)
                    __gitcomp "'*' none" "" "${cur#assignee=}"
                    __git_spindle_collaborators "${previous_args[1]}" "${cur#assignee=}"
                    ;;
                mentioned=*)
                    __git_spindle_collaborators "${previous_args[1]}" "${cur#mentioned=}"
                    ;;
                labels=*)
                    ;;
                sort=*)
                    __gitcomp "created updated comments created" "" "${cur#sort=}"
                    ;;
                direction=*)
                    __gitcomp "asc desc" "" "${cur#direction=}"
                    ;;
                since=*)
                    ;;
                number=*)
                    ;;
                etag=*)
                    ;;
                *)
                    __gitcompadd "milestone= state= assignee= mentioned= labels= sort= direction= since= number= etag=" "" "$cur"
                    ;;
            esac
            ;;
        lab,*)
            case "$cur" in
                state=*)
                    __gitcomp "all opened closed" "" "${cur#state=}"
                    ;;
                labels=*)
                    ;;
                labels_name=*)
                    __gitcomp "No+Label" "" "${cur#labels_name=}"
                    ;;
                milestone=*)
                    ;;
                order_by=*)
                    __gitcomp "created_at updated_at" "" "${cur#order_by=}"
                    ;;
                sort=*)
                    __gitcomp "asc desc" "" "${cur#sort=}"
                    ;;
                *)
                    __gitcompadd "state= labels= labels_name= milestone= order_by= sort=" "" "$cur"
                    ;;
            esac
            ;;
    esac
}

_git_spindle_log() {
    case "$1,$prev" in
        hub,--type)
            unset COMPREPLY
            __gitcomp "
                CommitComment
                Create
                Delete
                Download
                Follow
                Fork
                ForkApply
                Gist
                GistHistory
                Gollum
                IssueComment
                Issues
                Member
                OrgBlock
                ProjectCard
                ProjectColumn
                Project
                Public
                PullRequest
                PullRequestReview
                PullRequestReviewComment
                Push
                Release
                Watch
            "
            ;;
        hub,--count)
            unset COMPREPLY
            ;;
        hub,*)
            __git_spindle_options "--type= --count=" no_space
            __git_spindle_options "--verbose" && return

            [ ${#previous_args[@]} -eq 1 ] || return

            __git_spindle_collaborators "" "$cur"
            __git_spindle_repos $1 no_own
            ;;
        lab,*)
            __git_spindle_options && return

            [ ${#previous_args[@]} -eq 1 ] || return

            __git_spindle_repos $1
            ;;
    esac
}

_git_spindle_ls() {
    __git_spindle_options || _filedir -d
}

_git_spindle_members() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_merge_request() {
    __git_spindle_options "--yes" && return

    [ ${#previous_args[@]} -eq 1 ] || return

    case "$cur" in
        *:*:*)
            ;;
        *:*)
            case " $(echo $(git remote)) " in
                *\ upstream\ *)
                    __gitcomp_nl "$(git for-each-ref --format='%(refname:strip=3)' refs/remotes/upstream)" "" "${cur#*:}"
                    ;;
                *)
                    __gitcomp_nl "$(git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin)" "" "${cur#*:}"
                    ;;
            esac
            ;;
        *)
            __gitcomp_nl "$(__git_heads)" "" "$cur" ":"
            ;;
    esac
}

_git_spindle_mirror() {
    __git_spindle_protocols $1
    __git_spindle_options "--goblet" && return

    [ ${#previous_args[@]} -eq 1 ] || return

    __git_spindle_repos $1
    case $1 in
        hub|bb)
            case "$cur" in
                */)
                    __gitcompappend "$cur*" "" "$cur" " "
                    ;;
            esac
            ;;
        lab)
            __gitcompappend "'*'" "" "$cur" " "
            ;;
    esac
}

_git_spindle_privileges() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_protect() {
    case "$1,$prev" in
        hub,--enforcement-level)
            unset COMPREPLY
            __gitcomp "everyone non_admins"
            return
            ;;
        hub,--contexts)
            unset COMPREPLY
            return
            ;;
        hub,*)
            __git_spindle_options "--enforcement-level= --contexts=" no_space
            ;;
    esac

    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __gitcomp_nl "$(__git_heads)"
}

_git_spindle_pull_request() {
    case "$1,$prev" in
        hub,--issue)
            unset COMPREPLY

            [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

            local IFS=$'\n\r'
            local -a issues=($(git hub issues --parent 2>/dev/null || git hub issues 2>/dev/null))
            issues=("${issues[@]##Issues *}")
            issues=("${issues[@]##*/pull/*}")
            issues=("${issues[@]#[}")
            __gitcomp_nl_append "${issues[*]%%]*}"
            return
            ;;
        hub,*)
            __git_spindle_options "--issue=" no_space
            __git_spindle_options "--yes" && return
            ;;
        *)
            __git_spindle_options "--yes" && return
            ;;
    esac

    [ ${#previous_args[@]} -eq 1 ] || return

    case "$cur" in
        *:*:*)
            ;;
        *:*)
            case " $(echo $(git remote)) " in
                *\ upstream\ *)
                    __gitcomp_nl "$(git for-each-ref --format='%(refname:strip=3)' refs/remotes/upstream)" "" "${cur#*:}"
                    ;;
                *)
                    __gitcomp_nl "$(git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin)" "" "${cur#*:}"
                    ;;
            esac
            ;;
        *)
            __gitcomp_nl "$(__git_heads)" "" "$cur" ":"
            ;;
    esac
}

_git_spindle_readme() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_release() {
    __git_spindle_options "--draft --prerelease" && return

    [ ${#previous_args[@]} -eq 1 ] && __gitcomp_nl "$(git for-each-ref --format='%(refname:strip=2)' refs/tags)"
}

_git_spindle_releases() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_repos $1
}

_git_spindle_remove_collaborator() {
    __git_spindle_options && return

    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n\r'
    local -a issues=($(git hub collaborators 2>/dev/null))
    __gitcomp_nl_append "${issues[*]%%]*}"
}

_git_spindle_remove_deploy_key() {
    __git_spindle_options && return

    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n'
    local -a deploy_keys=($(git $1 deploy-keys 2>/dev/null))
    deploy_keys=("${deploy_keys[@]##*id: }")
    __gitcomp_nl_append "${deploy_keys[*]%%,*}"
}

_git_spindle_remove_hook() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __git_spindle_hooks
}

_git_spindle_remove_member() {
    __git_spindle_options && return

    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n'
    local -a members=($(git lab members 2>/dev/null))
    members=("${members[@]%% \(*}")
    IFS=' '
    __gitcomp "${members[*]#* }"
}

_git_spindle_remove_privilege() {
    __git_spindle_options && return

    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n'
    local -a members=($(git bb privileges 2>/dev/null))
    members=("${members[@]%% \(*}")
    IFS=' '
    __gitcomp "${members[*]#* }"
}

_git_spindle_render() {
    case "$prev" in
        --save)
            unset COMPREPLY
            _filedir '@(htm|html)'
            return
            ;;
        *)
            __git_spindle_options "--save=" no_space && return
            ;;
    esac

    [ ${#previous_args[@]} -eq 1 ] && _filedir '@(md)'
}

_git_spindle_repos() {
    __git_spindle_options "--no-forks"
}

_git_spindle_set_origin() {
    __git_spindle_set_origin $1
}

_git_spindle_snippet() {
    _git_spindle_gist
}

_git_spindle_unprotect() {
    __git_spindle_options && return

    [ ${#previous_args[@]} -eq 1 ] && __gitcomp_nl "$(__git_heads)"
}

##########################################################################

__git_spindle_set_previous_args() {
    __git_spindle_set_previous_args_or_options args "$1" $2
}

__git_spindle_set_previous_options() {
    __git_spindle_set_previous_args_or_options options "$1" $2
}

__git_spindle_set_previous_args_or_options() {
    local prev_word dummy
    for word in "${words[@]:2:$cword-2}"; do
        case "$prev_word,$3, $(eval "echo \${${3-dummy}[@]}") " in
            --account,*|*,?*,*\ $prev_word\ *)
                [ $1 = options ] && eval "$2[\${#$2[@]}]=$word"
                prev_word=
                continue
                ;;
        esac

        case $1,$word in
            options,--*)
                eval "$2[\${#$2[@]}]=$word"
                ;;
            options,*|*,--*)
                ;;
            *)
                eval "$2[\${#$2[@]}]=$word"
                ;;
        esac
        prev_word=$word
    done
}

__git_spindle_set_origin() {
    case "$prev" in
        --upstream-branch)
            unset COMPREPLY
            __gitcomp "$(git for-each-ref --format '%(refname:strip=3)' refs/remotes/upstream/)"
            return 1
            ;;
        *)
            __git_spindle_protocols $1
            __git_spindle_options "--triangular"
            __git_spindle_options "--upstream-branch=" no_space
            return 0
            ;;
    esac
}

__git_spindle_protocols() {
    case "$1" in
        hub)
            __git_spindle_options "--git --http --ssh"
            ;;
        *)
            __git_spindle_options "--http --ssh"
            ;;
    esac
}

__git_spindle_forks() {
    case "$1,${GIT_SPINDLE_COMPLETE_REMOTE-no}" in
        *,nos)
            ;;
        hub,*|bb,*)
            local IFS=$'\n'
            local -a forks=($(git $1 forks 2>/dev/null))
            forks=("${forks[@]#[}")
            __gitcomp_nl_append "${forks[*]%%]*}"
            ;;
    esac
}

__git_spindle_repos() {
    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local repos IFS=$'\n'
    case "$1,$cur" in
        # do not do anything
        # - if there are at least 2 slashes in $cur or
        # - if there is a slash in $cur and we are in "lab" mode,
        #   as "git lab" does not support requesting repos for a user, only own ones or
        # - if $cur starts with a slash
        *,*/*/*|lab,*/*|*,/*)
            ;;
        # for non "lab" if a slash with something in front is in &cur,
        # request the repos for that user
        *,*/*)
            repos=($(git $1 repos "${cur%/*}" 2>/dev/null))
            repos=(${repos[@]%% *})
            __gitcomp_nl_append "${repos[*]#*/}" "${cur%/*}/" "${cur#*/}"
            ;;
        *)
            # request the own repos if wanted
            if [ ${2-also_own} = also_own ]; then
                repos=($(git $1 repos 2>/dev/null))
                repos=(${repos[@]%% *})
                __gitcomp_nl_append "${repos[*]#*/}"
            fi

            # do not check for other users repos in "lab" mode, as it is not possible
            [ $1 = lab ] && return

            # request repos of user in $cur if something is present
            if [ -n "$cur" ]; then
                repos=($(git $1 repos "$cur" 2>/dev/null))
                repos=(${repos[@]%% *})
                __gitcomp_nl_append "${repos[*]#*/}" "$cur/" ""
            fi
            ;;
    esac
}

__git_spindle_hooks() {
    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n'
    hooks=($(git hub hooks 2>/dev/null))
    hooks=(${hooks[@]%% \(*})
    hooks=(${hooks[@]## *})
    __gitcompappend "${hooks[*]}" "" "$cur" " "
}

__git_spindle_hook_settings() {
    local hook_name="${previous_args[1]}"
    case "$hook_name,${GIT_SPINDLE_COMPLETE_REMOTE-no}" in
        web$1,*)
            case "$cur" in
                events=*,*)
                    local prefix="${cur#events=}"
                    __gitcomp "
                        '*'
                        commit_comment
                        create
                        delete
                        deployment
                        deployment_status
                        fork
                        gollum
                        issue_comment
                        issues
                        label
                        member
                        membership
                        milestone
                        organization
                        org_block
                        page_build
                        project_card
                        project_column
                        project
                        public
                        pull_request
                        pull_request_review
                        pull_request_review_comment
                        push
                        release
                        repository
                        status
                        team
                        team_add
                        watch
                    " "${prefix%,*}," "${cur##events=*,}"
                    ;;
                events=*)
                    __gitcomp "
                        '*'
                        commit_comment
                        create
                        delete
                        deployment
                        deployment_status
                        fork
                        gollum
                        issue_comment
                        issues
                        label
                        member
                        membership
                        milestone
                        organization
                        org_block
                        page_build
                        project_card
                        project_column
                        project
                        public
                        pull_request
                        pull_request_review
                        pull_request_review_comment
                        push
                        repository
                        release
                        status
                        team
                        team_add
                        watch
                    " "" "${cur##events=}"
                    ;;
                url=*)
                    __gitcompadd "http" "" "${cur#url=}"
                    ;;
                content_type=*)
                    __gitcomp "json form" "" "${cur#content_type=}"
                    ;;
                secret=*)
                    ;;
                insecure_ssl=*)
                    __gitcomp "0 1" "" "${cur#insecure_ssl=}"
                    ;;
                *)
                    __gitcompadd "events= url= content_type= secret= insecure_ssl=" "" "$cur"
                    ;;
            esac
            ;;
        *,no)
            ;;
        *)
            case "$cur" in
                events=*,*)
                    local IFS=$'\n\r'
                    local -a hook_settings=($(DEBUG=1 git hub available-hooks $hook_name 2>/dev/null))
                    unset IFS
                    local prefix="${cur#events=}"
                    __gitcomp "'*' ${hook_settings[0]}" "${prefix%,*}," "${cur##events=*,}"
                    ;;
                events=*)
                    local IFS=$'\n\r'
                    local -a hook_settings=($(DEBUG=1 git hub available-hooks $hook_name 2>/dev/null))
                    unset IFS
                    __gitcomp "'*' ${hook_settings[0]}" "" "${cur##events=}"
                    ;;
                *=*)
                    ;;
                *)
                    local IFS=$'\n\r'
                    local -a hook_settings=($(DEBUG=1 git hub available-hooks $hook_name 2>/dev/null))
                    unset IFS
                    __gitcompadd "events= ${hook_settings[1]}" "" "$cur"
                    ;;
            esac
            ;;
    esac
}

__git_spindle_collaborators() {
    [ ${GIT_SPINDLE_COMPLETE_REMOTE-no} = no ] && return

    local IFS=$'\n\r'
    __gitcompappend "$(git hub collaborators $1 2>/dev/null)" "" "$2" " "
}

__git_spindle_options() {
    case "$cur" in
        --*)
            case "$2" in
                overwrite)
                    __gitcompadd "$1" "" "$cur" " "
                    ;;
                no_space)
                    __gitcompappend "$1" "" "$cur"
                    ;;
                no_space*overwrite|overwrite*no_space)
                    __gitcompadd "$1" "" "$cur"
                    ;;
                *)
                    __gitcompappend "$1" "" "$cur" " "
                    ;;
            esac
            ;;
        *)
            return 1
            ;;
    esac
}

# for compatibility to Git < 1.7.9
declare -f __gitcomp_nl >/dev/null || __gitcomp_nl() {
    COMPREPLY=()
    __gitcomp_nl_append "$@"
}

# for compatibility to Git < 1.9.0
declare -f __gitcomp_nl_append >/dev/null || __gitcomp_nl_append() {
    local IFS=$'\n'
    __gitcompappend "$1" "${2-}" "${3-$cur}" "${4- }"
}

# for compatibility to Git < 1.8.3
declare -f __gitcompadd >/dev/null || __gitcompadd() {
    COMPREPLY=()
    __gitcompappend "$@"
}

# for compatibility to Git < 1.9.0
declare -f __gitcompappend >/dev/null || __gitcompappend() {
    local x i=${#COMPREPLY[@]}
    for x in $1; do
        if [[ "$x" == "$3"* ]]; then
            COMPREPLY[i++]="$2$x$4"
        fi
    done
}

# for compatibility to older bash-completion versions
declare -f _split_longopt >/dev/null || _split_longopt() {
    if [[ "$cur" == --?*=* ]]; then
        prev="${cur%%?(\\)=*}"
        cur="${cur#*=}"
        return 0
    fi
    return 1
}
