---
name: content-writing
description: Guide for writing blog posts and project pages for the Development Seed website. Use when creating or editing content in content/blog/ or content/project/ directories, or when the user asks for help writing blog posts or project pages.
---

# Development Seed Content Writing Guide

This skill helps you write blog posts and project pages following Development Seed's content standards and brand voice. For technical formatting details (MDX blocks, frontmatter, file naming), see the `content-formatting` skill.

## Content Structure

All blog posts and project pages should follow this narrative arc:

### 1. Lead Paragraph
- Hook the reader with the core challenge or opportunity
- Summarize the key insight or solution
- Set expectations for what follows

### 2. Problem/Challenge
- Start with the real-world problem being solved
- Use concrete examples and scenarios
- Explain why existing approaches fall short

### 3. Technical Approach
- Explain the solution clearly, assuming intermediate technical knowledge
- Use diagrams, screenshots, and code examples
- Break complex concepts into digestible sections with clear subheadings
- Link to external references for specialized concepts

### 4. Solution in Action
- Show real implementations and results
- Include visualizations (maps, charts, UI screenshots)
- Highlight collaboration with partners and clients
- Emphasize open source tools and contributions

### 5. Impact & Next Steps
- Wrap up with real-world impact
- Mention future work or opportunities
- End with calls to action: "Get in touch", "Check out our GitHub", "Explore the demo"

## Voice & Tone

Based on analysis of existing Development Seed content:

### Professional but Approachable
- Technical depth without unnecessary jargon
- Explain acronyms and specialized terms on first use
- Write for an audience of practitioners and decision-makers
- Assume readers have technical literacy but may not be domain experts

### Problem-Solution Focused
- Lead with challenges, not technologies
- Frame technical choices as solutions to real problems
- Show why the approach matters, not just how it works

### Collaborative & Open
- Emphasize partnerships with clients and the community
- Highlight open source contributions and tools
- Credit collaborators and external tools/APIs
- Link to GitHub repos, live demos, and related projects

### Impact-Oriented
- Connect technical work to real-world outcomes
- Mention environmental, social, or scientific impact
- Focus on democratizing access to geospatial data and tools
- Highlight how work serves underserved communities or advances science

## Common Content Patterns

### Technical Blog Posts typically include:
- Problem statement with concrete example
- Technical architecture or approach explanation
- Code snippets or API examples (when relevant)
- Diagrams showing workflows or system architecture
- Screenshots of tools/interfaces in action
- Links to GitHub repos, documentation, live demos
- "Future work" section mentioning ongoing development
- CTA: "Want to collaborate? Get in touch"

### Project Pages typically include:
- Client/partner introduction
- Challenge section explaining the core problem
- Overview of the solution and technologies used
- Outcome section highlighting impact and results
- Links to live project and source code (if available)
- Related blog posts or projects

## Coaching Technical Authors

Many Development Seed colleagues are deeply technical but may write in ways that lose non-technical audiences. When reviewing or coaching technical writing, help authors make content more accessible while maintaining technical accuracy.

### Common Issues in Technical Writing

**1. Jargon Without Context**
- **Problem**: Assumes reader knows specialized terms
- **Example**: "We implemented a STAC catalog with COG optimization for the GeoTIFF pipeline"
- **Better**: "We built a searchable catalog of satellite imagery (STAC) that loads faster by optimizing how images are stored (Cloud Optimized GeoTIFFs)"
- **Guidance**: Explain acronyms on first use, add brief context for specialized terms

**2. Leading with Technology Instead of Problems**
- **Problem**: "We used PostgreSQL with PostGIS extensions"
- **Better**: "We needed to query millions of geographic locations efficiently, so we used a database optimized for spatial data"
- **Guidance**: Start with the "why" before the "what". What problem does this solve?

**3. Assuming Domain Knowledge**
- **Problem**: "The vector tiles reduced bandwidth significantly"
- **Better**: "Instead of sending complete map data, we send only the pieces needed for the current view—like streaming video instead of downloading the whole movie"
- **Guidance**: Use analogies, explain concepts before using them

**4. Missing the "So What?"**
- **Problem**: Lists features without explaining impact
- **Better**: Connect technical work to outcomes (faster analysis, more accessible tools, environmental impact, cost savings)
- **Guidance**: Ask "What can users do now that they couldn't before?" and "Who benefits from this?"

**5. Dense, Unbroken Technical Explanations**
- **Problem**: Long paragraphs of technical details without breaks
- **Better**: Break into sections, use diagrams, provide concrete examples
- **Guidance**: Add subheadings, use `<PullQuote>` to highlight key insights, include visualizations

### Review Checklist for Accessibility

When reviewing technical content, check:

- [ ] **First paragraph accessible**: Can a non-specialist understand the core problem and solution?
- [ ] **Acronyms explained**: Every acronym defined on first use
- [ ] **Concepts before terminology**: Problems explained before introducing technical solutions
- [ ] **Analogies or examples**: Complex concepts illustrated with familiar comparisons
- [ ] **Impact stated clearly**: Real-world outcomes explicitly mentioned
- [ ] **Visual breaks**: Diagrams, screenshots, or pull quotes break up dense text
- [ ] **Progressive detail**: Start broad, get specific; don't require specialist knowledge upfront
- [ ] **Links to external resources**: Referenced tools, APIs, and concepts link to documentation

### Coaching Approach

When working with technical authors:

1. **Preserve technical accuracy**: Never sacrifice correctness for simplicity
2. **Add context, don't remove detail**: Explain before diving deep
3. **Show, don't tell**: Suggest specific rewording rather than just noting "too technical"
4. **Use analogies**: Offer comparisons to familiar concepts
5. **Highlight the narrative**: Help authors see the story (problem → approach → solution → impact)

### Example Rewrites

**Original** (too technical):
> "Our implementation leverages a distributed task queue with Redis as the message broker, enabling asynchronous processing of geospatial transformations with horizontal scalability."

**Improved** (accessible):
> "Processing large satellite images can take hours. To handle multiple requests simultaneously, we built a system that distributes the work across multiple servers—like having multiple checkout lanes at a grocery store instead of just one. This means users get their results faster, and the system can grow as demand increases."

**Original** (missing context):
> "We used Terraform for infrastructure as code deployment to AWS."

**Improved** (explains why):
> "Managing cloud infrastructure manually is error-prone and hard to replicate. We wrote our infrastructure setup as code (using Terraform), which means we can recreate our entire system with a single command—making it easier to test changes, recover from failures, and share our approach with others."

## Content Workflow

1. **Check existing content for context**
   - Read 2-3 recent blog posts in `content/blog/posts/2025/` to understand current voice and topics
   - For projects, review `content/project/posts/` for structure examples

2. **Plan content structure**
   - Write lead paragraph that hooks reader and summarizes key points
   - Outline the problem/challenge section
   - Plan technical approach with appropriate depth
   - Identify visuals needed (diagrams, screenshots)
   - Draft impact statement and CTA

3. **Write with accessibility in mind**
   - Explain acronyms on first use
   - Use analogies for complex concepts
   - Break into logical sections with clear subheadings
   - Include external links to tools, APIs, papers

4. **Review against checklist**
   - First paragraph accessible to non-specialists
   - Technical concepts explained before using terminology
   - Impact and outcomes clearly stated
   - Professional but approachable tone maintained

## Examples from Existing Content

See `content/blog/posts/2025/2025-01-29-llms.mdx` for an excellent example of:
- Problem/solution narrative structure
- Use of `<PullQuote>` to highlight key concepts
- Technical depth with accessibility
- Collaboration and trust-building themes
- Links to external projects and APIs
- Future work section
- Clear CTA at the end

See `content/project/posts/2024-06-05-clay.mdx` for project page structure.
