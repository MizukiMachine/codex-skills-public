#!/usr/bin/env python3
"""
Skill Initializer - Creates a new skill from template

Usage:
    init_skill.py <skill-name> --path <path> [--resources scripts,references,assets] [--examples] [--interface key=value]

Examples:
    init_skill.py my-new-skill --path skills/public
    init_skill.py my-new-skill --path skills/public --resources scripts,references
    init_skill.py my-api-helper --path skills/private --resources scripts --examples
    init_skill.py custom-skill --path /custom/location
    init_skill.py my-skill --path skills/public --interface short_description="Short UI label"
"""

import argparse
import re
import sys
from pathlib import Path

from generate_openai_yaml import write_openai_yaml

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_RESOURCES = {"scripts", "references", "assets"}

SKILL_TEMPLATE = """---
name: {skill_name}
description: "TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it."
---

# {skill_title}

## Purpose

[TODO: 1-2 sentences explaining what this skill enables]

## Operating Model

[TODO: Add the mental model, philosophy, priority hierarchy, or contract that should guide this work. State what matters most and what common proxy goal to avoid.]

Before acting, establish:
- [TODO: Question or fact that changes the correct approach]
- [TODO: Constraint, audience, input shape, framework, or artifact state to inspect]
- [TODO: Success criteria or output quality bar]

## What, Why, and Deliverables

**What it does**: [TODO: State the capability in operational terms.]

**Why use it**: [TODO: State the recurring pain, quality gap, or task class this improves.]

**Deliverables**:
- [TODO: File, edit, report, asset, decision, or other concrete output]
- [TODO: Verification output or acceptance signal]

## Workflow

[TODO: Replace with the real workflow. If this skill works on an existing codebase, document discovery before generation.]

1. [TODO: Analyze the user's request and inspect required artifacts]
2. [TODO: Choose the approach using the operating model]
3. [TODO: Execute with the appropriate scripts, references, or assets]
4. [TODO: Verify the output using the checks below]

{reference_files_section}

## Patterns and Examples

[TODO: Add concrete examples, command patterns, code snippets, decision tables, or output shapes. Prefer examples that teach judgment over generic prose.]

## Anti-Patterns

[TODO: List predictable weak outputs. For each one, include what to avoid, why it fails, and the better replacement.]

Example:

**Generic output that ignores context**

Why bad: It produces work that could fit any project and misses the user's actual constraints.

Better: Inspect the relevant artifact first, extract the constraints, and adapt the output.

## Variation Guidance

[TODO: Explain what should change by context so Codex does not collapse into one template.]

Vary based on:
- [TODO: Framework, platform, audience, artifact type, risk level, or style]

Avoid converging on:
- [TODO: Repetitive layout, phrasing, command, code pattern, or assumption]

## Verification

[TODO: Add the commands, preview steps, validators, tests, screenshots, or acceptance checks that prove the skill worked.]

{resources_section}
"""

REFERENCE_FILES_SECTION_WITH_EXAMPLE = """## Reference Files

Link every reference directly from SKILL.md and explain when to read it.

| Topic | File | Use When |
|-------|------|----------|
| [TODO] | [api_reference.md](references/api_reference.md) | [TODO] |
"""

REFERENCE_FILES_SECTION_EMPTY = """## Reference Files

Link every reference directly from SKILL.md and explain when to read it.

| Topic | File | Use When |
|-------|------|----------|
| [TODO] | `references/[TODO].md` | [TODO] |
"""

NO_RESOURCES_SECTION = """## Resources (optional)

No resource directories were created. Add only the directories this skill genuinely needs:

- `scripts/` for repeatable executable mechanics
- `references/` for detailed documentation Codex should load conditionally
- `assets/` for templates, images, fonts, or other files used in final output
"""

SCRIPTS_RESOURCE_SECTION = """### scripts/

Executable code that can be run directly for deterministic or repeated operations.

Appropriate for: analyzers, generators, converters, validators, preview tools, and other automation that would otherwise be rewritten.

Document the exact command, expected inputs and outputs, and validation steps.
"""

REFERENCES_RESOURCE_SECTION = """### references/

Documentation and reference material loaded into context only when needed.

Appropriate for: API docs, schemas, framework-specific guides, audit checklists, detailed workflows, and troubleshooting maps.

Link each reference from SKILL.md with clear "Use When" guidance.
"""

ASSETS_RESOURCE_SECTION = """### assets/

Files not intended to be loaded into context, but used within the output Codex produces.

Appropriate for: templates, boilerplate projects, images, icons, fonts, sample data, and reusable design assets.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}

This is a placeholder script that can be executed directly.
Replace with actual implementation or delete if not needed.

Example real scripts from other skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images
"""

def main():
    print("This is an example script for {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

Use references for material that is important but too detailed or conditional
for the main SKILL.md body.

If this file grows beyond roughly 100 lines, add a table of contents and make
the section headings easy to search with `rg`.

## Use When

- [TODO: Name the situation where Codex should read this reference]
- [TODO: Name the artifact, framework, feature, or failure mode this file covers]

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Anti-patterns and troubleshooting
- Verification steps

### Framework or Variant Guide Example
- How to detect this framework or variant
- File locations and integration points
- Minimal implementation pattern
- Common pitfalls
- Validation commands
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Codex produces.

Example asset files from other skills:
- Brand guidelines: logo.png, slides_template.pptx
- Frontend builder: hello-world/ directory with HTML/React boilerplate
- Typography: custom-font.ttf, font-family.woff2
- Data: sample_data.csv, test_dataset.json

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml

Note: This is a text placeholder. Actual assets can be any file type.
"""


def normalize_skill_name(skill_name):
    """Normalize a skill name to lowercase hyphen-case."""
    normalized = skill_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def build_reference_files_section(resources, include_examples):
    """Return the Reference Files section only when references are requested."""
    if "references" not in resources:
        return ""
    if include_examples:
        return REFERENCE_FILES_SECTION_WITH_EXAMPLE
    return REFERENCE_FILES_SECTION_EMPTY


def build_resources_section(resources, include_examples):
    """Return a Resources section that matches the directories created."""
    if not resources:
        return NO_RESOURCES_SECTION

    sections = ["## Resources\n\nResource directories created for this skill:\n"]
    section_by_resource = {
        "scripts": SCRIPTS_RESOURCE_SECTION,
        "references": REFERENCES_RESOURCE_SECTION,
        "assets": ASSETS_RESOURCE_SECTION,
    }
    for resource in resources:
        sections.append(section_by_resource[resource])

    if include_examples:
        sections.append(
            "Customize or delete placeholder files and sections that do not directly support the skill.\n"
        )
    else:
        sections.append("Delete sections that do not directly support the skill.\n")
    return "\n".join(sections)


def parse_resources(raw_resources):
    if not raw_resources:
        return []
    resources = [item.strip() for item in raw_resources.split(",") if item.strip()]
    invalid = sorted({item for item in resources if item not in ALLOWED_RESOURCES})
    if invalid:
        allowed = ", ".join(sorted(ALLOWED_RESOURCES))
        print(f"[ERROR] Unknown resource type(s): {', '.join(invalid)}")
        print(f"   Allowed: {allowed}")
        sys.exit(1)
    deduped = []
    seen = set()
    for resource in resources:
        if resource not in seen:
            deduped.append(resource)
            seen.add(resource)
    return deduped


def create_resource_dirs(skill_dir, skill_name, skill_title, resources, include_examples):
    for resource in resources:
        resource_dir = skill_dir / resource
        resource_dir.mkdir(exist_ok=True)
        if resource == "scripts":
            if include_examples:
                example_script = resource_dir / "example.py"
                example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
                example_script.chmod(0o755)
                print("[OK] Created scripts/example.py")
            else:
                print("[OK] Created scripts/")
        elif resource == "references":
            if include_examples:
                example_reference = resource_dir / "api_reference.md"
                example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
                print("[OK] Created references/api_reference.md")
            else:
                print("[OK] Created references/")
        elif resource == "assets":
            if include_examples:
                example_asset = resource_dir / "example_asset.txt"
                example_asset.write_text(EXAMPLE_ASSET)
                print("[OK] Created assets/example_asset.txt")
            else:
                print("[OK] Created assets/")


def init_skill(skill_name, path, resources, include_examples, interface_overrides):
    """
    Initialize a new skill directory with template SKILL.md.

    Args:
        skill_name: Name of the skill
        path: Path where the skill directory should be created
        resources: Resource directories to create
        include_examples: Whether to create example files in resource directories

    Returns:
        Path to created skill directory, or None if error
    """
    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"[ERROR] Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"[OK] Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"[ERROR] Error creating directory: {e}")
        return None

    # Create SKILL.md from template
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title,
        reference_files_section=build_reference_files_section(resources, include_examples),
        resources_section=build_resources_section(resources, include_examples),
    )

    skill_md_path = skill_dir / "SKILL.md"
    try:
        skill_md_path.write_text(skill_content)
        print("[OK] Created SKILL.md")
    except Exception as e:
        print(f"[ERROR] Error creating SKILL.md: {e}")
        return None

    # Create agents/openai.yaml
    try:
        result = write_openai_yaml(skill_dir, skill_name, interface_overrides)
        if not result:
            return None
    except Exception as e:
        print(f"[ERROR] Error creating agents/openai.yaml: {e}")
        return None

    # Create resource directories if requested
    if resources:
        try:
            create_resource_dirs(skill_dir, skill_name, skill_title, resources, include_examples)
        except Exception as e:
            print(f"[ERROR] Error creating resource directories: {e}")
            return None

    # Print next steps
    print(f"\n[OK] Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    if resources:
        resource_list = ", ".join(f"{resource}/" for resource in resources)
        if include_examples:
            print(f"2. Customize or delete the example files in {resource_list}")
        else:
            print(f"2. Add resources to {resource_list} as needed")
    else:
        print("2. Create resource directories only if needed (scripts/, references/, assets/)")
    print("3. Update agents/openai.yaml if the UI metadata should differ")
    print("4. Run the validator when ready to check the skill structure")
    print(
        "5. Forward-test complex skills with realistic user requests to ensure they work as intended"
    )

    return skill_dir


def main():
    parser = argparse.ArgumentParser(
        description="Create a new skill directory with a SKILL.md template.",
    )
    parser.add_argument("skill_name", help="Skill name (normalized to hyphen-case)")
    parser.add_argument("--path", required=True, help="Output directory for the skill")
    parser.add_argument(
        "--resources",
        default="",
        help="Comma-separated list: scripts,references,assets",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Create example files inside the selected resource directories",
    )
    parser.add_argument(
        "--interface",
        action="append",
        default=[],
        help="Interface override in key=value format (repeatable)",
    )
    args = parser.parse_args()

    raw_skill_name = args.skill_name
    skill_name = normalize_skill_name(raw_skill_name)
    if not skill_name:
        print("[ERROR] Skill name must include at least one letter or digit.")
        sys.exit(1)
    if len(skill_name) > MAX_SKILL_NAME_LENGTH:
        print(
            f"[ERROR] Skill name '{skill_name}' is too long ({len(skill_name)} characters). "
            f"Maximum is {MAX_SKILL_NAME_LENGTH} characters."
        )
        sys.exit(1)
    if skill_name != raw_skill_name:
        print(f"Note: Normalized skill name from '{raw_skill_name}' to '{skill_name}'.")

    resources = parse_resources(args.resources)
    if args.examples and not resources:
        print("[ERROR] --examples requires --resources to be set.")
        sys.exit(1)

    path = args.path

    print(f"Initializing skill: {skill_name}")
    print(f"   Location: {path}")
    if resources:
        print(f"   Resources: {', '.join(resources)}")
        if args.examples:
            print("   Examples: enabled")
    else:
        print("   Resources: none (create as needed)")
    print()

    result = init_skill(skill_name, path, resources, args.examples, args.interface)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
