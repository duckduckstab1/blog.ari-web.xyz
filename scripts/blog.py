#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manage blogs"""

import hashlib
import os
import random
import string
import sys
import xml.etree.ElementTree as etree
from base64 import b64decode, b64encode
from datetime import datetime
from glob import iglob
from html import escape as html_escape
from re import Match as RegexMatch
from shutil import copy as copy_file
from shutil import rmtree
from tempfile import gettempdir
from threading import Thread
from timeit import default_timer as code_timer
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple
from warnings import filterwarnings as filter_warnings

import ujson  # type: ignore
from css_html_js_minify import html_minify  # type: ignore
from css_html_js_minify import process_single_css_file  # type: ignore
from markdown import core as markdown_core  # type: ignore
from markdown import markdown  # type: ignore
from markdown.extensions import Extension  # type: ignore
from markdown.inlinepatterns import InlineProcessor  # type: ignore
from markdown.treeprocessors import Treeprocessor  # type: ignore
from plumbum.commands.processes import ProcessExecutionError  # type: ignore
from pyfzf import FzfPrompt  # type: ignore

NOT_CI_BUILD: bool = not os.getenv("CI")

if NOT_CI_BUILD:
    import readline
    from atexit import register as fn_register

EXIT_OK: int = 0
EXIT_ERR: int = 1

DEFAULT_CONFIG: Dict[str, Any] = {
    "editor-command": f"{os.environ.get('EDITOR', 'vim')} -- %s",
    "blog-dir": "b",
    "git-url": "/git",
    "py-markdown-extensions": [
        "markdown.extensions.abbr",
        "markdown.extensions.def_list",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.md_in_html",
        "markdown.extensions.tables",
        "markdown.extensions.admonition",
        "markdown.extensions.sane_lists",
        "markdown.extensions.toc",
        "markdown.extensions.wikilinks",
        "pymdownx.betterem",
        "pymdownx.caret",
        "pymdownx.magiclink",
        "pymdownx.mark",
        "pymdownx.tilde",
    ],
    "default-keywords": ["website", "blog", "opinion", "article", "ari-web", "ari"],
    "page-title": "Ari::web -> Blog",
    "page-description": "My blog page",
    "colourscheme-type": "dark",
    "short-name": "Ari's blogs",
    "home-keywords": ["ari", "ari-web", "blog", "ari-archer", "foss", "free", "linux"],
    "base-homepage": "https://ari-web.xyz/",
    "meta-icons": [{"src": "/favicon.ico", "sizes": "128x128", "type": "image/png"}],
    "theme-colour": "#f9f6e8",
    "background-colour": "#262220",
    "full-name": "Ari Archer",
    "locale": "en_GB",
    "home-page-header": "My blogs",
    "comment-url": "/c",
    "blogs": {},
}
DEFAULT_CONFIG_FILE: str = "blog.json"
HISTORY_FILE: str = ".blog_history"
BLOG_VERSION: int = 1

BLOG_MARKDOWN_TEMPLATE: str = """<header role="group">
    <h1 role="heading" aria-level="1">%s</h1>

    <nav id="info-bar" role="menubar">
        <a role="menuitem" aria-label="jump to the main content" href="#main">\
skip</a>
        <span role="seperator" aria-hidden="true">|</span>

        <span role="menuitem"><time>%s</time> GMT</span>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="/">home</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="%s">comment</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="%s">website</a>
        <span role="seperator" aria-hidden="true">|</span>

        <a role="menuitem" href="%s">git</a>

        <hr aria-hidden="true" role="seperator" />
    </nav>
</header>

<article id="main">

<!-- Main blog content: Begin -->

%s

<!-- Main blog content: End -->

</article>"""

HTML_HEADER: str = f"""<head>
    <meta charset="UTF-8"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

    <meta property="og:locale" content="{{locale}}"/>

    <meta name="color-scheme" content="{{theme_type}}"/>
    <meta name="author" content="{{author}}"/>
    <meta name="keywords" content="{{keywords}}"/>
    <meta name="robots" content="follow, index, max-snippet:-1, \
max-video-preview:-1, max-image-preview:large"/>
    <meta name="generator" \
content="Ari-web blog generator version {BLOG_VERSION}"/>

    <link
        rel="stylesheet"
        href="/content/styles.min.css"
        referrerpolicy="no-referrer"
        type="text/css"
        hreflang="en"
    />
"""

BLOG_HTML_TEMPLATE: str = f"""<!DOCTYPE html>
<html lang="en">
{HTML_HEADER}
    <title>{{title}} -> {{blog_title}}</title>

    <meta name="description" content="{{blog_description}}"/>
    <meta property="og:type" content="article"/>
</head>
<body>
    <main id="blog-content">

{{blog}}

    </main>
</body>
</html>"""

HOME_PAGE_HTML_TEMPLATE: str = f"""<!DOCTYPE html>
<html lang="en">
{HTML_HEADER}
    <title>{{title}}</title>

    <meta name="description" content="{{home_page_description}}"/>
    <meta property="og:type" content="website"/>

    <link
        rel="manifest"
        href="/manifest.json"
        referrerpolicy="no-referrer"
        type="application/json"
        hreflang="en"
    />
</head>
<body>
    <header>
        <h1 role="heading" aria-level="1">{{page_header}}</h1>

        <nav id="info-bar" role="navigation">
            <p role="menubar">
                <a
                    role="menuitem"
                    aria-label="jump to the main content"
                    href="#main"
                >skip</a>

                <span aria-hidden="true" role="seperator">|</span>

                <span role="menuitem">
                    latest update: <time>{{lastest_blog_time}}</time> GMT
                </span>

                <span aria-hidden="true" role="seperator">|</span>

                <span role="menuitem">
                    latest blog: \
                    <a href="{{latest_blog_url}}">{{latest_blog_title}}</a>
                </span>

                <span aria-hidden="true" role="seperator">|</span>

                <a role="menuitem" href="{{git_url}}">git</a>
            </p>

            <hr aria-hidden="true" role="seperator" />
        </nav>
    </header>

    <main id="main">

<!-- Main home page content: Begin -->

{{content}}

<!-- Main home page content: End -->

    </main>
</body>
</html>"""


def sanitise_title(title: str, titleset: Iterable[str], _nosep: bool = False) -> str:
    _title: str = ""

    for char in title:
        _title += (
            char
            if char not in string.whitespace + string.punctuation
            else "-"
            if _title and _title[-1] != "-"
            else ""
        )

    _title = _title.lower().rstrip("-")

    return (
        _title
        if _title not in titleset and _title.strip()
        else sanitise_title(
            _title + ("" if _nosep else "-") + random.choice(string.digits),
            titleset,
            True,
        )
    )


def truncate_str(string: str, length: int) -> str:
    if len(string) <= length:
        return string

    return string[:length] + "..."


class BetterHeaders(Treeprocessor):
    """Better headers

    - Downsizes headers from h1 -> h2
    - Adds header links"""

    def run(self, root: etree.Element) -> None:
        ids: List[str] = []
        heading_sizes_em: Dict[str, float] = {
            "h2": 1.32,
            "h3": 1.15,
            "h4": 1.0,
            "h5": 0.87,
            "h6": 0.76,
        }

        for idx, elem in enumerate(root):
            if elem.tag == "h1":
                elem.tag = "h2"

            if elem.tag not in heading_sizes_em:
                continue

            if elem.text is None:
                elem.text = ""

            gen_id: str = sanitise_title(elem.text, ids)
            ids.append(gen_id)

            heading_parent: etree.Element = elem.makeelement(
                "div",
                {
                    "data-pl": "",
                    "style": f"font-size:{(heading_sizes_em[elem.tag] + 0.1):.2f}".strip(
                        "0"
                    ).rstrip(
                        "."
                    )
                    + "em",
                },
            )

            heading: etree.Element = heading_parent.makeelement(
                elem.tag, {"id": gen_id}
            )
            link: etree.Element = heading.makeelement(
                "a",
                {
                    "href": f"#{gen_id}",
                    "aria-hidden": "true",
                    "focusable": "false",
                    "tabindex": "-1",
                },
            )

            link.text = "#"
            heading.text = elem.text

            heading_parent.extend(
                (
                    link,
                    heading,
                )
            )
            root.remove(elem)
            root.insert(idx, heading_parent)


class AddIDLinks(InlineProcessor):
    """Add support for <#ID> links"""

    def handleMatch(  # pyright: ignore
        self, match: RegexMatch, *_  # pyright: ignore
    ) -> Tuple[etree.Element, Any, Any]:
        link: etree.Element = etree.Element("a")

        link.text = match.group(1) or "#"
        link.set("href", link.text or "#")

        return link, match.start(0), match.end(0)


class AriMarkdownExts(Extension):
    """Ari-web markdown extensions"""

    def extendMarkdown(
        self,
        md: markdown_core.Markdown,
        key: str = "add_header_links",
        index: int = int(1e8),
    ):
        md.registerExtension(self)

        md.treeprocessors.register(
            BetterHeaders(md.parser), key, index  # pyright: ignore
        )
        md.inlinePatterns.register(
            AddIDLinks(r"<(#.*)>", "a"), key, index  # pyright: ignore
        )


def log(message: str, header: str = "ERROR", code: int = EXIT_ERR) -> int:
    if not (not NOT_CI_BUILD and header != "ERROR"):
        sys.stderr.write(f"{header}: {message}\n")

    return code


def tmp_path(path: str) -> str:
    return os.path.join(gettempdir(), path)


def editor(config: Dict[str, Any], file: str) -> None:
    copy_file(".editorconfig", tmp_path(".editorconfig"))
    os.system(config["editor-command"] % file)


def format_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def iinput(prompt: str, default_text: str = "") -> str:
    default_text = default_text.strip()

    def hook():
        if not default_text:
            return

        readline.insert_text(default_text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    user_inpt: str = input(f"({prompt}) ").strip()
    readline.set_pre_input_hook()

    return user_inpt


def yn(prompt: str, default: str = "y", current_value: str = "") -> bool:
    return (
        iinput(
            f"{prompt}? ({'y/n'.replace(default.lower(), default.upper())})",
            current_value,
        )
        + default
    ).lower()[0] == "y"


def new_config() -> None:
    log("Making new config...", "INFO")

    with open(DEFAULT_CONFIG_FILE, "w") as cfg:
        ujson.dump(DEFAULT_CONFIG, cfg, indent=4)


def pick_blog(config: Dict[str, Any]) -> str:
    try:
        blog_id: str = (
            FzfPrompt()
            .prompt(  # pyright: ignore
                map(
                    lambda key: f"{key} | {b64decode(config['blogs'][key]['title']).decode()!r}",  # pyright: ignore
                    tuple(config["blogs"].keys())[::-1],
                ),
                "--prompt='Pick blog: '",
            )[0]
            .split()[0]  # pyright: ignore
        )
    except ProcessExecutionError:
        log("Fzf process exited unexpectedly")
        return ""

    if blog_id not in config["blogs"]:
        log(f"Blog {blog_id!r} does not exist")
        return ""

    return blog_id


def new_blog(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Make a new blog"""

    if title := iinput("blog title"):
        readline.add_history(title)

        us_title: str = title
        s_title: str = sanitise_title(us_title, config["blogs"])
    else:
        raise RuntimeError("Unreachable")

    blog: Dict[str, Any] = {
        "title": b64encode(us_title.encode()).decode(),
        "content": "",
        "version": BLOG_VERSION,
        "time": 0.0,
        "keywords": "",
    }

    file: str = tmp_path(f"{s_title}.md")

    open(file, "w").close()
    editor(config, file)

    if not os.path.isfile(file):
        return log(f"{file!r} does not exist"), config

    with open(file, "r") as md:
        blog["content"] = b64encode(md.read().encode()).decode()

    os.remove(file)

    if not blog["content"].strip():  # type: ignore
        return log("Blog cannot be empty"), config

    user_keywords: str = iinput("keywords (seperated by spaces)")
    readline.add_history(user_keywords)

    blog["keywords"] = html_escape(user_keywords)

    blog["time"] = datetime.now().timestamp()
    config["blogs"][s_title] = blog

    return EXIT_OK, config


def build_css(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Minify (build) the CSS"""

    log("Minifying CSS...", "MINIFY")

    saved_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    css_threads: List[Thread] = []

    def _thread(t: Callable[..., Any]) -> None:
        css_threads.append(Thread(target=t, daemon=True))
        css_threads[-1].start()

    if os.path.isfile("content/styles.css"):
        log("Minifying main styles", "MINIFY")
        _thread(
            lambda: process_single_css_file("content/styles.css")  # pyright: ignore
        )

    if os.path.isdir("content/fonts"):
        log("Minifying fonts...", "MINIFY")

        for font in iglob("content/fonts/*.css"):
            if font.endswith(".min.css"):
                continue

            log(f"Minifying font file: {font}", "MINIFY")
            _thread(lambda: process_single_css_file(font))  # pyright: ignore

    for t in css_threads:
        t.join()

    sys.stdout.close()
    sys.stdout = saved_stdout

    log("Done minifying CSS", "MINIFY")

    return EXIT_OK, config


def build(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Build, minimise and generate site"""

    if not config["blogs"]:
        return log("No blogs to build"), config

    latest_blog_id: str = tuple(config["blogs"].keys())[-1]

    if os.path.isdir(config["blog-dir"]):
        rmtree(config["blog-dir"])

    os.makedirs(config["blog-dir"], exist_ok=True)

    log("Building blogs...", "INFO")

    def thread(blog_id: str, blog_meta: Dict[str, Any]):
        if blog_meta["version"] != BLOG_VERSION:
            log(
                f"{blog_id}: unmatching version between \
{blog_meta['version']} and {BLOG_VERSION}",
                "WARNING",
            )

        blog_dir: str = os.path.join(config["blog-dir"], blog_id)
        os.makedirs(blog_dir, exist_ok=True)

        with open(os.path.join(blog_dir, "index.html"), "w") as blog_html:
            blog_time: str = format_time(blog_meta["time"])

            blog_title: str = html_escape(b64decode(blog_meta["title"]).decode())

            blog_base_html: str = markdown(
                BLOG_MARKDOWN_TEMPLATE
                % (
                    blog_title,
                    blog_time,
                    config["comment-url"],
                    config["base-homepage"],
                    config["git-url"],
                    markdown(
                        b64decode(blog_meta["content"]).decode(),
                        extensions=[
                            *config["py-markdown-extensions"],
                            AriMarkdownExts(),
                        ],
                    )
                    .replace("<pre>", '<pre focusable="true" role="code" tabindex="0">')
                    .replace(
                        "<blockquote>", '<blockquote focusable="true" tabindex="0">'
                    ),
                )
            )

            blog_html_full: str = BLOG_HTML_TEMPLATE.format(
                title=config["page-title"],
                theme_type=config["colourscheme-type"],
                keywords=blog_meta["keywords"].replace(" ", ", ")
                + ", "
                + ", ".join(config["default-keywords"]),
                blog_description=f"Blog on {blog_time} GMT -- {blog_title}",
                blog_title=blog_title,
                blog=blog_base_html,
                author=config["full-name"],
                locale=config["locale"],
            )

            log(f"Minifying {blog_id!r} HTML", "MINIFY")
            blog_html_full = html_minify(blog_html_full)
            log(f"Done minifying the HTML of {blog_id!r}", "MINIFY")

            blog_html.write(blog_html_full)

        log(f"Finished building blog {blog_id!r}", "BUILD")

    _tmp_threads: List[Thread] = []

    for blog_id, blog_meta in config["blogs"].items():
        t: Thread = Thread(target=thread, args=(blog_id, blog_meta), daemon=True)
        t.start()

        _tmp_threads.append(t)

    for awaiting_thread in _tmp_threads:
        awaiting_thread.join()

    log("Building blog index...", "INFO")

    with open("index.html", "w") as index:
        lastest_blog: Dict[str, Any] = config["blogs"][latest_blog_id]
        lastest_blog_time: str = format_time(lastest_blog["time"])

        blog_list = '<ol reversed="true" aria-label="latest blogs">'

        for blog_id, blog_meta in reversed(config["blogs"].items()):
            blog_list += f'<li><a href="{os.path.join(config["blog-dir"], blog_id)}">{html_escape(b64decode(blog_meta["title"]).decode())}</a></li>'

        blog_list += "</ol>"

        index.write(
            html_minify(
                HOME_PAGE_HTML_TEMPLATE.format(
                    title=config["page-title"],
                    theme_type=config["colourscheme-type"],
                    keywords=", ".join(config["home-keywords"])
                    + ", "
                    + ", ".join(config["default-keywords"]),
                    home_page_description=config["page-description"],
                    lastest_blog_time=lastest_blog_time,
                    latest_blog_url=os.path.join(config["blog-dir"], latest_blog_id),
                    latest_blog_title=truncate_str(
                        b64decode(html_escape(lastest_blog["title"])).decode(), 20
                    ),
                    git_url=config["git-url"],
                    content=blog_list,
                    author=config["full-name"],
                    locale=config["locale"],
                    page_header=config["home-page-header"],
                )
            )
        )

    return EXIT_OK, config


def list_blogs(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """List blogs"""

    if not config["blogs"]:
        return log("No blogs to list"), config

    for blog_id, blog_meta in config["blogs"].items():
        print(
            f"""ID: {blog_id}
Title: {b64decode(blog_meta["title"]).decode()!r}
Version: {blog_meta["version"]}
Time_of_creation: {format_time(blog_meta["time"])}
Keywords: {blog_meta['keywords'].replace(" ", ", ")}
"""
        )

    return EXIT_OK, config


def remove_blog(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Remove a blog page"""

    if not config["blogs"]:
        return log("No blogs to remove"), config

    blog_id: str = pick_blog(config)

    if not blog_id:
        return EXIT_ERR, config

    del config["blogs"][blog_id]
    return EXIT_OK, config


def dummy(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Print help/usage information"""

    return EXIT_OK, config


def edit_title(blog: str, config: Dict[str, Any]) -> int:
    new_title: str = iinput(
        "edit title", b64decode(config["blogs"][blog]["title"]).decode()
    )

    if not new_title.strip():
        return log("New title cannot be empty")

    # Made it not change the slug

    # old_blog: dict = config["blogs"][blog].copy()
    # old_blog["title"] = b64encode(new_title.encode()).decode()
    # del config["blogs"][blog]

    # config["blogs"][sanitise_title(new_title, config["blogs"])] = old_blog
    # del old_blog

    config["blogs"][blog]["title"] = b64encode(new_title.encode()).decode()

    return EXIT_OK


def edit_keywords(blog: str, config: Dict[str, Any]) -> int:
    new_keywords: str = iinput("edit keywords", config["blogs"][blog]["keywords"])

    if not new_keywords.strip():
        return log("Keywords cannot be empty")

    config["blogs"][blog]["keywords"] = new_keywords

    return EXIT_OK


def edit_content(blog: str, config: Dict[str, Any]) -> int:
    file: str = tmp_path(f"{blog}.md")

    with open(file, "w") as blog_md:
        blog_md.write(b64decode(config["blogs"][blog]["content"]).decode())

    editor(config, file)

    with open(file, "r") as blog_md_new:
        content: str = blog_md_new.read()

        if not content.strip():
            blog_md_new.close()
            return log("Content of a blog cannot be empty")

        config["blogs"][blog]["content"] = b64encode(content.encode()).decode()

    return EXIT_OK


EDIT_HOOKS: Dict[str, Callable[[str, Dict[str, Any]], int]] = {
    "quit": lambda *_: EXIT_OK,  # pyright: ignore
    "title": edit_title,
    "keywords": edit_keywords,
    "content": edit_content,
}


def edit(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Edit a blog"""

    if not config["blogs"]:
        return log("No blogs to edit"), config

    blog_id: str = pick_blog(config)

    if not blog_id:
        return EXIT_ERR, config

    try:
        hook: str = FzfPrompt().prompt(  # pyright: ignore
            EDIT_HOOKS.keys(), "--prompt='What to edit: '"
        )[0]

        if hook not in EDIT_HOOKS:
            return log(f"Hook {hook!r} does not exist"), config

        EDIT_HOOKS[hook](blog_id, config)
    except ProcessExecutionError:
        return log("No blog selected"), config

    return EXIT_OK, config


def gen_def_config(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Generate default config"""

    if os.path.exists(DEFAULT_CONFIG_FILE):
        if iinput("Do you want to overwite config? (y/n)").lower()[0] != "y":
            return log("Not overwritting config", "INFO", EXIT_OK), config

    new_config()

    with open(DEFAULT_CONFIG_FILE, "r") as cfg:
        config = ujson.load(cfg)

    return EXIT_OK, config


def clean(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Clean up current directory"""

    TRASH: Set[str] = {
        HISTORY_FILE,
        config["blog-dir"],
        "index.html",
        "content/*.min.*",
        "blog_json_hash.txt",
        "manifest.json",
        "content/fonts/*.min.*",
    }

    def remove(file: str) -> None:
        log(f"Removing {file!r}", "REMOVE")

        try:
            os.remove(file)
        except IsADirectoryError:
            rmtree(file)

    for glob_ex in TRASH:
        for file in iglob(glob_ex, recursive=True):
            remove(file)

    open(HISTORY_FILE, "w").close()

    return EXIT_OK, config


def generate_metadata(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Generate metadata"""

    with open("manifest.json", "w") as manifest:
        log(f"Generating {manifest.name}...", "GENERATE")
        ujson.dump(
            {
                "$schema": "https://json.schemastore.org/web-manifest-combined.json",
                "short_name": config["short-name"],
                "name": config["page-title"],
                "description": config["page-description"],
                "icons": config["meta-icons"],
                "start_url": ".",
                "display": "standalone",
                "theme_color": config["theme-colour"],
                "background_color": config["background-colour"],
            },
            manifest,
        )

    with open(DEFAULT_CONFIG_FILE, "rb") as blog_api_file:
        log(f"Generating hash for {DEFAULT_CONFIG_FILE!r}", "HASH")

        with open(
            f"{DEFAULT_CONFIG_FILE.replace('.', '_')}_hash.txt", "w"
        ) as blog_api_hash:
            blog_api_hash.write(hashlib.sha256(blog_api_file.read()).hexdigest())

    return EXIT_OK, config


def generate_static_full(config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Generate full static site"""

    BUILD_CFG: Dict[str, Callable[[Dict[str, Any]], Tuple[int, Dict[str, Any]]]] = {
        "Cleaning up": clean,
        "Building CSS": build_css,
        "Building static site": build,
        "Generating metatata": generate_metadata,
    }

    for logger_msg, function in BUILD_CFG.items():
        log(f"{logger_msg}...", "STATIC")
        code, config = function(config)

        if code != EXIT_OK:
            log("Failed to generate static site")
            return EXIT_ERR, config

    return EXIT_OK, config


SUBCOMMANDS: Dict[str, Callable[[Dict[str, Any]], Tuple[int, Dict[str, Any]]]] = {
    "help": dummy,
    "new": new_blog,
    "build": build,
    "ls": list_blogs,
    "rm": remove_blog,
    "edit": edit,
    "defcfg": gen_def_config,
    "clean": clean,
    "metadata": generate_metadata,
    "static": generate_static_full,
    "css": build_css,
}


def usage(code: int = EXIT_ERR, _: Optional[Dict[str, Any]] = None) -> int:
    sys.stderr.write(f"Usage: {sys.argv[0]} <subcommand>\n")

    for subcommand, func in SUBCOMMANDS.items():
        sys.stderr.write(f"  {subcommand:20s}{func.__doc__ or ''}\n")

    return code


def main() -> int:
    """Entry/main function"""

    if NOT_CI_BUILD:
        if not os.path.isfile(HISTORY_FILE):
            open(HISTORY_FILE, "w").close()

        readline.parse_and_bind("tab: complete")

        fn_register(readline.write_history_file, HISTORY_FILE)
        fn_register(readline.read_history_file, HISTORY_FILE)

        readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(5000)

        readline.set_auto_history(False)

    if not os.path.isfile(DEFAULT_CONFIG_FILE):
        new_config()
        log(f"PLease configure {DEFAULT_CONFIG_FILE!r}")
        return EXIT_ERR

    if len(sys.argv) != 2:
        return usage()
    elif sys.argv[1] not in SUBCOMMANDS:
        return log(f"{sys.argv[1]!r} is not a subcommand, try `{sys.argv[0]} help`")
    elif sys.argv[1] == "help":
        return usage(EXIT_OK)

    with open(DEFAULT_CONFIG_FILE, "r") as lcfg:
        cmd_time_init = code_timer()

        code: int
        config: Dict[str, Any]

        code, config = SUBCOMMANDS[sys.argv[1]](ujson.load(lcfg))

        log(
            f"Finished in {code_timer() - cmd_time_init} seconds with code {code}",
            "TIME",
        )

        if config["blogs"] and NOT_CI_BUILD:
            log("Sorting blogs by creation time...", "CLEANUP")

            sort_timer = code_timer()

            config["blogs"] = dict(
                map(
                    lambda k: (k, config["blogs"][k]),
                    sorted(config["blogs"], key=lambda k: config["blogs"][k]["time"]),
                )
            )

            log(f"Sorted in {code_timer() - sort_timer} seconds", "TIME")

        log("Redumping config", "CONFIG")

        dump_timer = code_timer()

        with open(DEFAULT_CONFIG_FILE, "w") as dcfg:
            ujson.dump(config, dcfg, indent=(4 if NOT_CI_BUILD else 0))

        log(f"Dumped config in {code_timer() - dump_timer} seconds", "TIME")

    return code


if __name__ == "__main__":
    assert main.__annotations__.get("return") is int, "main() should return an integer"

    filter_warnings("error", category=Warning)
    sys.exit(main())
