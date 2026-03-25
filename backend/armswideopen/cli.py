"""CLI for OpenArms."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from armswideopen.sdk import AuthenticationError, HfApi, HubError, hf_hub_download


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_login(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    token = api.login(args.username, args.password)
    print(f"Logged in as {args.username}")
    if args.show_token:
        print(token)
    return 0


def cmd_logout(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    api.logout()
    print("Logged out")
    return 0


def cmd_whoami(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    _print_json(api.whoami())
    return 0


def cmd_list_models(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    models = api.list_models(search=args.search, limit=args.limit)
    _print_json(models)
    return 0


def cmd_create_model(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    repo = api.create_repo(
        args.repo_id,
        repo_type="model",
        private=args.private,
        name=args.name,
        description=args.description,
    )
    _print_json(repo)
    return 0


def cmd_create_dataset(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    repo = api.create_repo(
        args.repo_id,
        repo_type="dataset",
        private=args.private,
        name=args.name,
        description=args.description,
    )
    _print_json(repo)
    return 0


def cmd_upload_file(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    result = api.upload_file(
        path_or_fileobj=args.path,
        path_in_repo=args.path_in_repo or args.path.split("/")[-1],
        repo_id=args.repo_id,
        repo_type=args.repo_type,
    )
    _print_json(result)
    return 0


def cmd_download_file(args: argparse.Namespace) -> int:
    api = HfApi(endpoint=args.endpoint)
    file_path = hf_hub_download(
        repo_id=args.repo_id,
        filename=args.filename,
        revision=args.revision,
        token=api.token,
        local_dir=args.local_dir,
        endpoint=args.endpoint,
    )
    print(file_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="armswideopen", description="OpenArms CLI")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000",
        help="Hub API endpoint (default: http://localhost:8000)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    login = subparsers.add_parser("login", help="Login and store token")
    login.add_argument("username")
    login.add_argument("password")
    login.add_argument("--show-token", action="store_true")
    login.set_defaults(func=cmd_login)

    logout = subparsers.add_parser("logout", help="Clear stored authentication")
    logout.set_defaults(func=cmd_logout)

    whoami = subparsers.add_parser("whoami", help="Show current authenticated user")
    whoami.set_defaults(func=cmd_whoami)

    list_models = subparsers.add_parser("list-models", help="List models")
    list_models.add_argument("--search", default=None)
    list_models.add_argument("--limit", type=int, default=20)
    list_models.set_defaults(func=cmd_list_models)

    create_model = subparsers.add_parser("create-model", help="Create a model repository")
    create_model.add_argument("repo_id", help="Model ID, e.g. username/model-name")
    create_model.add_argument("--name", default=None)
    create_model.add_argument("--description", default=None)
    create_model.add_argument("--private", action="store_true")
    create_model.set_defaults(func=cmd_create_model)

    create_dataset = subparsers.add_parser("create-dataset", help="Create a dataset repository")
    create_dataset.add_argument("repo_id", help="Dataset ID, e.g. username/dataset-name")
    create_dataset.add_argument("--name", default=None)
    create_dataset.add_argument("--description", default=None)
    create_dataset.add_argument("--private", action="store_true")
    create_dataset.set_defaults(func=cmd_create_dataset)

    upload_file = subparsers.add_parser("upload-file", help="Upload a file to a model repository")
    upload_file.add_argument("repo_id")
    upload_file.add_argument("path")
    upload_file.add_argument("--path-in-repo", default=None)
    upload_file.add_argument("--repo-type", choices=["model", "dataset"], default="model")
    upload_file.set_defaults(func=cmd_upload_file)

    download_file = subparsers.add_parser("download-file", help="Download a file from a model repository")
    download_file.add_argument("repo_id")
    download_file.add_argument("filename")
    download_file.add_argument("--revision", default="main")
    download_file.add_argument("--local-dir", default=None)
    download_file.set_defaults(func=cmd_download_file)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        exit_code = args.func(args)
    except AuthenticationError as exc:
        print(f"Authentication error: {exc}", file=sys.stderr)
        exit_code = 2
    except HubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 1
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        exit_code = 130
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
