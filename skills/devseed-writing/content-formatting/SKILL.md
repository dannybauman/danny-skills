---
name: content-formatting
description: Technical guide for MDX formatting, frontmatter, file naming, and block layouts for the Development Seed website. Use when creating new content files, checking formatting requirements, or troubleshooting MDX structure in content/blog/ or content/project/ directories.
---

# Development Seed Content Formatting Guide

This skill covers the technical requirements for blog posts and project pages: file structure, frontmatter, MDX blocks, and image handling.

## Technical Documentation References

**IMPORTANT**: For detailed technical specifications, always reference these documentation files:

- **[docs/CONTENT.md](../../docs/CONTENT.md)**: Complete frontmatter specifications for blog posts, projects, team members, and other content types. Includes all required and optional fields.
- **[docs/BLOCK_LAYOUT.md](../../docs/BLOCK_LAYOUT.md)**: Detailed documentation on all MDX block types (`<Text>`, `<PullQuote>`, `<Media>`, `<Diptych>`, `<FeatureList>`, `<NumberList>`, `<BrowserMedia>`), their properties, and usage examples.
- **[docs/DEVELOPMENT.md](../../docs/DEVELOPMENT.md)**: Development environment setup and build process (only reference if needed for testing).

Read these files when you need specific technical details about frontmatter fields or block layout syntax.

## File Structure & Naming

### File Naming Convention
All content files follow: `YYYY-MM-DD-slug-name.mdx`

**Locations:**
- Blog posts: `content/blog/posts/<year>/YYYY-MM-DD-slug.mdx`
- Blog images: `content/blog/media/<year>/`
- Project pages: `content/project/posts/YYYY-MM-DD-slug.mdx`
- Project images: `content/project/media/`

### Getting Slugs
- **Author slugs**: From team member filename `2020-01-01-ian-schuler.mdx` → `ian-schuler`
- **Blog post slugs**: Full filename without extension `2025-01-29-llms.mdx` → `2025-01-29-llms`
- **Project slugs**: Filename without date `2024-06-05-clay.mdx` → `clay`

### Image Requirements
- **Aspect ratio**: 2:1 recommended for cover images
- **Minimum width**: 1920px for cover/featured images
- **Format**: JPG, PNG, or WebP

### Image Paths
Always use `require()` syntax:
- **Blog**: `src={require("../../media/2025/image.jpg")}`
- **Project**: `src={require("../media/image.jpg")}`

## Approved Topics

**Blog topics**: Team, Data & AI/ML, Environment, Society, Cloud Computing & Infrastructure, Geospatial Technology & Products

**Project topics**: Labs, Data & AI/ML, Environment, Society, Cloud Computing & Infrastructure, Geospatial Technology & Products

## MDX Block Layout

**CRITICAL**: Never use plain markdown. All content must be wrapped in MDX blocks.

### Available Blocks

| Block | Purpose |
|-------|---------|
| `<Text>` | Main body content, multiple paragraphs, subheadings |
| `<PullQuote>` | Highlight key insights, quotes, or technical concepts |
| `<Media>` | Images, diagrams, visualizations |
| `<BrowserMedia>` | UI screenshots, application demos (with browser chrome) |
| `<Diptych>` | Side-by-side explanations with supporting images |
| `<FeatureList>` | Listing capabilities or features |
| `<NumberList>` | Highlighting statistics or metrics |

### Recommended Block Usage

- `<Text>`: Main body content, multiple paragraphs, subheadings
- `<PullQuote>`: Highlight key insights, quotes, or technical concepts (1-2 per post)
- `<Media size="large">`: Workflow diagrams, architecture diagrams, data visualizations
- `<BrowserMedia>`: UI screenshots, application demos
- `<Diptych>`: Side-by-side explanations with supporting images
- `<FeatureList>`: When listing capabilities or features
- `<NumberList>`: When highlighting statistics or metrics

Refer to [docs/BLOCK_LAYOUT.md](../../docs/BLOCK_LAYOUT.md) for complete syntax and examples.

## Formatting Checklist

When creating or reviewing content files, verify:

### Frontmatter
- [ ] All required fields present (check [docs/CONTENT.md](../../docs/CONTENT.md))
- [ ] Topic is from approved list
- [ ] Author slugs match team member files
- [ ] Teaser under 150 characters
- [ ] Date in YYYY-MM-DD format

### Images
- [ ] Images exist at specified paths
- [ ] Images meet size requirements (2:1 ratio, min 1920px for covers)
- [ ] All images use `require()` syntax with correct relative paths

### MDX Structure
- [ ] All content wrapped in MDX blocks (no plain markdown)
- [ ] All blocks properly opened and closed
- [ ] Correct nesting of markdown within blocks
- [ ] Links formatted correctly

### File Location
- [ ] File in correct directory (`content/blog/posts/<year>/` or `content/project/posts/`)
- [ ] Filename follows `YYYY-MM-DD-slug.mdx` convention
- [ ] Associated images in correct media folder

## Common Formatting Errors

### Missing Block Wrapper
```mdx
<!-- WRONG -->
This is some text about our project.

<!-- CORRECT -->
<Text>
This is some text about our project.
</Text>
```

### Incorrect Image Path
```mdx
<!-- WRONG -->
<Media src="image.jpg" />
<Media src="/media/2025/image.jpg" />

<!-- CORRECT -->
<Media src={require("../../media/2025/image.jpg")} />
```

### Unclosed Block
```mdx
<!-- WRONG -->
<Text>
Some content here...
<!-- missing </Text> -->

<!-- CORRECT -->
<Text>
Some content here...
</Text>
```
