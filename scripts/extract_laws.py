"""
Extraction script for Laws of Software Engineering (https://lawsofsoftwareengineering.com/)
Extracts all laws grouped by theme into Markdown files.
"""

import html
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://lawsofsoftwareengineering.com/'
OUTPUT_DIR = Path('laws-of-software-engineering')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def html_to_markdown_inline(text: str) -> str:
    if not text:
        return ''
    # Convert links
    text = re.sub(
        r'<a\s+[^>]*href=[\"\'\']?([^\"\'\'\s>]+)[\"\'\']?[^>]*>(.*?)</a>',
        r'[\2](\1)',
        text,
        flags=re.DOTALL,
    )
    # Strong / b
    text = re.sub(
        r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', text, flags=re.DOTALL
    )
    # Em / i
    text = re.sub(
        r'<(?:em|i)>(.*?)</(?:em|i)>', r'*\1*', text, flags=re.DOTALL
    )
    # Code
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    # Strip any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def fetch_and_parse_law(session: requests.Session, law_info: dict) -> dict:
    url = law_info['url']
    r = session.get(url, timeout=15)
    if r.status_code != 200:
        print(f'Warning: failed to fetch {url} (status: {r.status_code})')
        return law_info

    page = r.text

    # Read time
    read_m = re.search(
        r'<div class=reading-time[^>]*>.*?<span>(.*?)</span>', page, re.DOTALL
    )
    law_info['read_time'] = read_m.group(1).strip() if read_m else ''

    # Lead statement
    lead_m = re.search(r'<p class=lead>(.*?)</p>', page, re.DOTALL)
    law_info['lead'] = (
        html_to_markdown_inline(lead_m.group(1))
        if lead_m
        else law_info['description']
    )

    # Takeaways
    takeaways_m = re.search(
        r'<section id=takeaways[^>]*>(.*?)</section>', page, re.DOTALL
    )
    if takeaways_m:
        lis = re.findall(r'<li>(.*?)</li>', takeaways_m.group(1), re.DOTALL)
        law_info['takeaways'] = [
            html_to_markdown_inline(li)
            for li in lis
            if html_to_markdown_inline(li)
        ]
    else:
        law_info['takeaways'] = []

    # Overview
    overview_m = re.search(
        r'<section id=overview[^>]*>(.*?)</section>', page, re.DOTALL
    )
    if overview_m:
        ps = re.findall(r'<p>(.*?)</p>', overview_m.group(1), re.DOTALL)
        law_info['overview'] = [
            html_to_markdown_inline(p) for p in ps if html_to_markdown_inline(p)
        ]
    else:
        law_info['overview'] = []

    # Examples
    examples_m = re.search(
        r'<section id=examples[^>]*>(.*?)</section>', page, re.DOTALL
    )
    if examples_m:
        ps = re.findall(r'<p>(.*?)</p>', examples_m.group(1), re.DOTALL)
        law_info['examples'] = [
            html_to_markdown_inline(p) for p in ps if html_to_markdown_inline(p)
        ]
    else:
        law_info['examples'] = []

    # Origins
    origins_m = re.search(
        r'<section id=origins[^>]*>(.*?)</section>', page, re.DOTALL
    )
    if origins_m:
        ps = re.findall(r'<p>(.*?)</p>', origins_m.group(1), re.DOTALL)
        law_info['origins'] = [
            html_to_markdown_inline(p) for p in ps if html_to_markdown_inline(p)
        ]
    else:
        law_info['origins'] = []

    # Further reading
    further_m = re.search(
        r'<section id=further-reading[^>]*>(.*?)</section>', page, re.DOTALL
    )
    readings = []
    if further_m:
        lis = re.findall(r'<li>(.*?)</li>', further_m.group(1), re.DOTALL)
        for li in lis:
            href_m = re.search(r'href=[\"\'\']?([^\"\'\'\s>]+)[\"\'\']?', li)
            t_m = re.search(r'<span class=reading-title>(.*?)</span>', li)
            d_m = re.search(r'<span class=reading-description>(.*?)</span>', li)
            href = href_m.group(1) if href_m else '#'
            rtitle = html_to_markdown_inline(t_m.group(1)) if t_m else 'Link'
            rdesc = html_to_markdown_inline(d_m.group(1)) if d_m else ''
            readings.append(
                {'title': rtitle, 'url': href, 'description': rdesc}
            )
    law_info['further_reading'] = readings

    # Related laws
    rel_m = re.search(
        r'<section id=related[^>]*>(.*?)</section>', page, re.DOTALL
    )
    related = []
    if rel_m:
        rcards = re.findall(
            r'<a\s+href=([^\s>]+)[^>]*>.*?<h3[^>]*>(.*?)</h3>',
            rel_m.group(1),
            re.DOTALL,
        )
        for rhref, rtitle in rcards:
            rslug = rhref.strip('/').split('/')[-1]
            related.append(
                {'slug': rslug, 'title': html_to_markdown_inline(rtitle)}
            )
    law_info['related_laws'] = related

    return law_info


def main():
    print(f'Fetching index from {BASE_URL}...')
    sess = requests.Session()
    sess.headers.update(
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )

    resp = sess.get(BASE_URL, timeout=15)
    resp.raise_for_status()

    card_pattern = r'<a\s+href=([^\s>]+)\s+class=law-card\s+data-group=([^\s>]+)\s+data-experience=([^\s>]+)[^>]*>.*?<h2[^>]*>(.*?)</h2>\s*<p[^>]*>(.*?)</p>'
    cards = re.findall(card_pattern, resp.text, re.DOTALL)
    print(f'Found {len(cards)} laws on index page.')

    laws_meta = []
    slug_to_law = {}

    for href, group, exp, title, desc in cards:
        href = href.strip()
        slug = href.strip('/').split('/')[-1]
        title_clean = html.unescape(re.sub(r'<[^>]+>', '', title)).strip()
        desc_clean = html.unescape(re.sub(r'<[^>]+>', '', desc)).strip()
        law_entry = {
            'slug': slug,
            'url': href,
            'group': group.strip(),
            'experience': exp.strip().capitalize(),
            'title': title_clean,
            'description': desc_clean,
        }
        laws_meta.append(law_entry)
        slug_to_law[slug] = law_entry

    print('Fetching and parsing individual law details...')
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(fetch_and_parse_law, sess, entry)
            for entry in laws_meta
        ]
        completed = 0
        for f in as_completed(futures):
            f.result()
            completed += 1
            if completed % 10 == 0 or completed == len(laws_meta):
                print(f'  Parsed {completed}/{len(laws_meta)} laws.')

    # Group by theme
    themes = {}
    for entry in laws_meta:
        themes.setdefault(entry['group'], []).append(entry)

    def get_law_link(slug, current_theme_file):
        target_meta = slug_to_law.get(slug)
        if not target_meta:
            return None
        target_theme = target_meta['group'].lower() + '.md'
        if target_theme == current_theme_file:
            return f'#{slug}'
        return f'{target_theme}#{slug}'

    print(f'Writing theme files to {OUTPUT_DIR}/...')
    for theme_name, laws in sorted(themes.items()):
        filename = f'{theme_name.lower()}.md'
        filepath = OUTPUT_DIR / filename
        lines = []
        lines.append(f'# Laws of Software Engineering — {theme_name}\n')
        lines.append(
            f'Extracted from [Laws of Software Engineering]({BASE_URL}). '
            f'This document covers all **{len(laws)}** principles categorized under **{theme_name}**.\n'
        )

        # Table of contents with valid markdown links
        lines.append('## Table of Contents\n')
        for l in laws:
            lines.append(
                f'- [{l["title"]}](#{l["slug"]}) — *{l["description"]}* ({l["experience"]})'
            )
        lines.append('\n---\n')

        # Detailed sections for each law
        for l in laws:
            lines.append(f'<a id="{l["slug"]}"></a>')
            lines.append(f'## {l["title"]}\n')
            meta_line = f'**Category:** {l["group"]} | **Level:** {l["experience"]}'
            if l.get('read_time'):
                meta_line += f' | **Read Time:** {l["read_time"]}'
            lines.append(f'> {meta_line}  ')
            lines.append(f'> **Source:** [{l["url"]}]({l["url"]})\n')

            if l.get('lead'):
                lines.append(f'**{l["lead"]}**\n')

            if l.get('takeaways'):
                lines.append('### Key Takeaways\n')
                for t in l['takeaways']:
                    lines.append(f'- {t}')
                lines.append('')

            if l.get('overview'):
                lines.append('### Overview\n')
                for p in l['overview']:
                    lines.append(f'{p}\n')

            if l.get('examples'):
                lines.append('### Examples\n')
                for p in l['examples']:
                    lines.append(f'{p}\n')

            if l.get('origins'):
                lines.append('### Origins\n')
                for p in l['origins']:
                    lines.append(f'{p}\n')

            if l.get('further_reading'):
                lines.append('### Further Reading\n')
                for fr in l['further_reading']:
                    if fr.get('description'):
                        lines.append(
                            f'- [{fr["title"]}]({fr["url"]}) — {fr["description"]}'
                        )
                    else:
                        lines.append(f'- [{fr["title"]}]({fr["url"]})')
                lines.append('')

            if l.get('related_laws'):
                lines.append('### Related Laws\n')
                for rl in l['related_laws']:
                    link = get_law_link(rl['slug'], filename)
                    if link:
                        lines.append(f'- [{rl["title"]}]({link})')
                    else:
                        lines.append(f'- {rl["title"]}')
                lines.append('')

            lines.append('---\n')

        filepath.write_text('\n'.join(lines), encoding='utf-8')
        print(f'  Created {filename} ({len(laws)} laws)')

    # Generate master README.md
    readme_path = OUTPUT_DIR / 'README.md'
    readme_lines = [
        '# Laws of Software Engineering\n',
        'Catalog of foundational laws, principles, and mental models in software engineering, extracted from [lawsofsoftwareengineering.com](https://lawsofsoftwareengineering.com/).\n',
        'The laws are organized by theme into individual markdown files:\n',
        '| Theme | File | Laws | Scope |',
        '|---|---|---|---|',
        '| **Architecture** | [architecture.md](architecture.md) | 9 | System boundaries, abstractions, distributed fallacies |',
        '| **Decisions** | [decisions.md](decisions.md) | 12 | Cognitive biases, mental models, tradeoffs |',
        '| **Design** | [design.md](design.md) | 6 | Code design, coupling, cohesion, SOLID, YAGNI, DRY |',
        '| **Planning** | [planning.md](planning.md) | 6 | Estimation, scope, optimization timing, metrics |',
        '| **Quality** | [quality.md](quality.md) | 11 | Testing, maintenance, technical debt, bugs |',
        '| **Scale** | [scale.md](scale.md) | 3 | Parallelism, network effects, scaling throughput |',
        '| **Teams** | [teams.md](teams.md) | 9 | Human dynamics, communication, organization, productivity |\n',
        '## Complete Index of Laws (56)\n',
        '| # | Law | Theme | Level | Summary |',
        '|---|---|---|---|---|',
    ]

    for idx, l in enumerate(laws_meta, 1):
        theme_file = f'{l["group"].lower()}.md'
        link = f'{theme_file}#{l["slug"]}'
        readme_lines.append(
            f'| {idx} | [{l["title"]}]({link}) | [{l["group"]}]({theme_file}) | {l["experience"]} | {l["description"]} |'
        )

    readme_lines.append('\n---\n')
    readme_lines.append(
        'Extracted automatically with key takeaways, overviews, examples, historical origins, further reading, and cross-references.\n'
    )

    readme_path.write_text('\n'.join(readme_lines), encoding='utf-8')
    print(f'  Created README.md (56 laws indexed)')
    print('Extraction completed successfully.')


if __name__ == '__main__':
    main()
