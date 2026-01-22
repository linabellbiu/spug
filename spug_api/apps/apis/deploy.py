# Copyright: (c) OpenSpug Organization. https://github.com/openspug/spug
# Copyright: (c) <spug.dev@gmail.com>
# Released under the AGPL-3.0 License.
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse
from apps.setting.utils import AppSetting
from apps.app.models import App
from apps.deploy.models import Deploy, DeployRequest
from apps.repository.models import Repository
from apps.deploy.utils import dispatch as deploy_dispatch
from libs.utils import human_datetime
from threading import Thread
import hashlib
import hmac
import json
import re


def auto_deploy(request, app_id):
    repo, body = _parse_request(request)
    if not repo:
        return HttpResponseForbidden()

    try:
        # 提取webhook请求中的仓库地址
        repo_url = _parse_repo_url(body, repo)
        
        # 判断是否是 merge request/pull request
        if _is_merge_request(body, repo):
            ref, commit_id, message = _parse_merge_request(body, repo)
            if ref and commit_id:
                Thread(target=_dispatch_by_branch, args=(app_id, ref, commit_id, message, repo_url)).start()
                return HttpResponse(status=202)
            return HttpResponse(status=204)
        
        # 处理普通的 push 事件（branch 或 tag）
        if 'ref' not in body:
            return HttpResponse(status=204)
            
        _, _kind, ref = body['ref'].split('/', 2)
        
        # Branch push
        if _kind == 'heads':
            commit_id = body.get('after', '')
            # 忽略删除分支的操作（commit_id 为全0）
            if commit_id and commit_id != '0000000000000000000000000000000000000000':
                message = _parse_message(body, repo)
                Thread(target=_dispatch_by_branch, args=(app_id, ref, commit_id, message, repo_url)).start()
                return HttpResponse(status=202)
        
        # Tag push
        elif _kind == 'tags':
            # 忽略删除 tag 的操作
            commit_id = body.get('after', '')
            if not commit_id or commit_id == '0000000000000000000000000000000000000000':
                return HttpResponse(status=204)
            Thread(target=_dispatch_by_branch, args=(app_id, ref, None, None, repo_url)).start()
            return HttpResponse(status=202)
        
        return HttpResponse(status=204)
    except Exception as e:
        return HttpResponseBadRequest(str(e))


def _parse_request(request):
    api_key = AppSetting.get_default('api_key')
    token, repo, body = None, None, None
    token = request.headers.get('X-Gitlab-Token')
    if 'X-Gitlab-Token' in request.headers:
        token = request.headers['X-Gitlab-Token']
        repo = 'Gitlab'
    elif 'X-Gitee-Token' in request.headers:
        token = request.headers['X-Gitee-Token']
        repo = 'Gitee'
    elif 'X-Codeup-Token' in request.headers:
        token = request.headers['X-Codeup-Token']
        repo = 'Codeup'
    elif 'X-Gitea-Signature' in request.headers:
        token = request.headers['X-Gitea-Signature']
        repo = 'Gitea'
    elif 'X-Gogs-Signature' in request.headers:
        token = request.headers['X-Gogs-Signature']
        repo = 'Gogs'
    elif 'X-Hub-Signature-256' in request.headers:
        token = request.headers['X-Hub-Signature-256'].replace('sha256=', '')
        repo = 'Github'
    elif 'X-Coding-Signature' in request.headers:
        token = request.headers['X-Coding-Signature'].replace('sha1=', '')
        repo = 'Coding'
    elif 'token' in request.GET:  # Compatible the old version of gitlab
        token = request.GET.get('token')
        repo = 'Gitlab'

    if repo in ['Gitlab', 'Gitee', 'Codeup']:
        if token != api_key:
            return None, None
    elif repo in ['Github', 'Gogs', 'Gitea']:
        en_api_key = hmac.new(api_key.encode(), request.body, hashlib.sha256).hexdigest()
        if token != en_api_key:
            return None, None
    elif repo in ['Coding']:
        en_api_key = hmac.new(api_key.encode(), request.body, hashlib.sha1).hexdigest()
        if token != en_api_key:
            return None, None
    else:
        return None, None

    body = json.loads(request.body)
    if repo in ['Gogs', 'Gitea'] and not body['ref'].startswith('refs/'):
        body['ref'] = 'refs/tags/' + body['ref']

    return repo, body


def _parse_message(body, repo):
    message = None
    if repo in ['Gitee', 'Github', 'Coding', 'Gitea']:
        message = body.get('head_commit', {}).get('message', '')
    elif repo in ['Gitlab', 'Codeup', 'Gogs']:
        if body.get('commits'):
            message = body['commits'][0].get('message', '')
    else:
        raise ValueError(f'repo {repo} is not supported')
    return message[:20].strip()


def _is_merge_request(body, repo):
    """判断是否是 merge request/pull request 事件"""
    if repo == 'Gitlab':
        return body.get('object_kind') == 'merge_request' and body.get('object_attributes', {}).get('action') == 'merge'
    elif repo == 'Gitee':
        return body.get('action') == 'merge' and 'pull_request' in body
    elif repo == 'Github':
        return body.get('action') == 'closed' and body.get('pull_request', {}).get('merged') is True
    elif repo == 'Coding':
        return body.get('action') == 'merge' and 'merge_request' in body
    elif repo == 'Codeup':
        return body.get('object_kind') == 'merge_request' and body.get('object_attributes', {}).get('action') == 'merge'
    return False


def _parse_merge_request(body, repo):
    """解析 merge request/pull request 信息，返回目标分支、commit_id 和消息"""
    try:
        if repo == 'Gitlab':
            attrs = body.get('object_attributes', {})
            ref = attrs.get('target_branch', '')
            commit_id = attrs.get('merge_commit_sha', '')
            message = f"Merge: {attrs.get('title', '')}"
        elif repo == 'Gitee':
            pr = body.get('pull_request', {})
            ref = pr.get('base', {}).get('ref', '')
            commit_id = pr.get('merge_commit_sha', '')
            message = f"Merge: {pr.get('title', '')}"
        elif repo == 'Github':
            pr = body.get('pull_request', {})
            ref = pr.get('base', {}).get('ref', '')
            commit_id = pr.get('merge_commit_sha', '')
            message = f"Merge: {pr.get('title', '')}"
        elif repo == 'Coding':
            mr = body.get('merge_request', {})
            ref = mr.get('target_branch', '')
            commit_id = mr.get('merge_commit_sha', '')
            message = f"Merge: {mr.get('title', '')}"
        elif repo == 'Codeup':
            attrs = body.get('object_attributes', {})
            ref = attrs.get('target_branch', '')
            commit_id = attrs.get('merge_commit_sha', '')
            message = f"Merge: {attrs.get('title', '')}"
        else:
            return None, None, None
        
        return ref, commit_id, message[:20].strip()
    except Exception:
        return None, None, None


def _parse_repo_url(body, repo):
    """从webhook payload中提取仓库地址"""
    try:
        if repo == 'Gitlab':
            project = body.get('project', {})
            return project.get('git_http_url') or project.get('http_url') or project.get('git_ssh_url') or project.get('ssh_url')
        elif repo == 'Gitee':
            repository = body.get('repository', {})
            return repository.get('url') or repository.get('html_url') or repository.get('ssh_url')
        elif repo == 'Github':
            repository = body.get('repository', {})
            return repository.get('clone_url') or repository.get('html_url') or repository.get('ssh_url')
        elif repo == 'Coding':
            repository = body.get('repository', {})
            return repository.get('https_url') or repository.get('ssh_url') or repository.get('web_url')
        elif repo == 'Codeup':
            project = body.get('project', {})
            return project.get('git_http_url') or project.get('http_url') or project.get('git_ssh_url') or project.get('ssh_url')
        elif repo in ['Gogs', 'Gitea']:
            repository = body.get('repository', {})
            return repository.get('clone_url') or repository.get('html_url') or repository.get('ssh_url')
        return None
    except Exception:
        return None


def _normalize_repo_url(url):
    """规范化仓库地址，去除协议、用户名、.git后缀等，便于比较"""
    if not url:
        return ''
    
    url = url.lower().strip()
    
    # 去除协议
    for prefix in ['https://', 'http://', 'git://', 'ssh://', 'git@']:
        if url.startswith(prefix):
            url = url[len(prefix):]
            break
    
    # 去除URL中的用户名和密码 (username:password@host 或 username@host)
    if '@' in url:
        # 找到最后一个@符号（因为密码中可能包含@）
        at_pos = url.rfind('@')
        # 检查@之前是否有斜杠，如果有说明@是路径的一部分而不是认证信息
        slash_before_at = url[:at_pos].rfind('/')
        if slash_before_at == -1:
            # @之前没有斜杠，说明是认证信息，去除它
            url = url[at_pos + 1:]
    
    # 处理 git@ 格式的 SSH URL (git@github.com:user/repo.git)
    url = url.replace(':', '/')
    
    # 去除 .git 后缀
    if url.endswith('.git'):
        url = url[:-4]
    
    # 去除末尾的斜杠
    url = url.rstrip('/')
    
    return url


def _dispatch_by_branch(app_id, ref, commit_id=None, message=None, repo_url=None):
    app = App.objects.filter(pk=app_id).first()
    if not app:
        raise Exception(f'no such app id for {app_id}')
    
    webhook_config = json.loads(app.webhook_config) if app.webhook_config else {}
    
    for env_id_str, branch_pattern in webhook_config.items():
        if not branch_pattern:
            continue
        
        env_id = int(env_id_str)
        
        if _match_branch(ref, branch_pattern):
            deploy = Deploy.objects.filter(app_id=app_id, env_id=env_id).first()
            if deploy:
                # 验证仓库地址是否匹配
                if not _match_repo_url(deploy, repo_url):
                    continue
                
                _dispatch(deploy.id, ref, commit_id, message)


def _match_branch(branch, pattern):
    if not pattern:
        return False
    
    pattern = pattern.strip()
    if not pattern:
        return False
    
    if pattern == '*':
        return True
    
    try:
        return re.match(pattern, branch) is not None
    except Exception:
        return branch == pattern


def _match_repo_url(deploy, webhook_repo_url):
    """验证webhook请求的仓库地址是否与部署配置的仓库地址匹配"""
    if not webhook_repo_url:
        return True
    
    # 获取部署配置中的仓库地址
    deploy_repo_url = None
    if deploy.extend in ('1', '3'):
        extend_obj = deploy.extend_obj
        if extend_obj and hasattr(extend_obj, 'git_repo'):
            deploy_repo_url = extend_obj.git_repo
    
    if not deploy_repo_url:
        return True
    
    # 规范化后比较
    normalized_webhook_url = _normalize_repo_url(webhook_repo_url)
    normalized_deploy_url = _normalize_repo_url(deploy_repo_url)
    
    return normalized_webhook_url == normalized_deploy_url


def _dispatch(deploy_id, ref, commit_id=None, message=None):
    deploy = Deploy.objects.filter(pk=deploy_id).first()
    if not deploy:
        raise Exception(f'no such deploy id for {deploy_id}')

    req = DeployRequest(
        type='3',
        status='0' if deploy.is_audit else '2',
        deploy=deploy,
        spug_version=Repository.make_spug_version(deploy.id),
        host_ids=deploy.host_ids,
        created_by=deploy.created_by
    )

    if commit_id:  # branch
        req.version = f'{ref}#{commit_id[:6]}'
        req.name = message or req.version
        if deploy.extend == '1':
            req.extra = json.dumps(['branch', ref, commit_id])
    else:  # tag
        req.version = ref
        req.name = ref
        if deploy.extend == '1':
            req.extra = json.dumps(['tag', ref, None])

    req.save()
    if req.status == '2':
        req.do_at = human_datetime()
        req.do_by = deploy.created_by
        req.save()
        deploy_dispatch(req)
