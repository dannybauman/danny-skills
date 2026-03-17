<h1 align="center">
  DS.O V5 - <small>Content</small>
</h1>

> [!TIP]
> Check the [templates](./TEMPLATES.md) for bootstrap content pieces.

- [📚 Content types](#-content-types)
  - [Anatomy of a MDX file](#anatomy-of-a-mdx-file)
  - [Organization of the content](#organization-of-the-content)
- [📝  Creating a new piece of content](#--creating-a-new-piece-of-content)
- [🏞 Image guidance](#-image-guidance)
- [📇 Adding properties to content](#-adding-properties-to-content)
  - [Blog](#blog)
  - [Project](#project)
  - [Expertise](#expertise)
  - [Team member](#team-member)
  - [Career](#career)
  - [Event](#event)

## 📚 Content types

All the dynamic content for the Devseed website is store inside the `content` folder and is written using MDX which is basically and extended version of [Markdown](https://www.markdownguide.org/).

The extended part of MDX means that you can embed special components in your markdown files to add interactivity to your content.


### Anatomy of a MDX file

A MDX file is a markdown file with the extension `.mdx`.
The file is made up of two parts: the `frontmatter` and the `content`. The frontmatter is a section of content at the top of the file that is enclosed in `---` and contains metadata about the file. The content is the main body of the file.

For example, this team member:
```md
---
title: Ian Schuler
description: >-
  Ian oversees our strategy and team to make sure we are doing meaningful,
  impactful work.
social:
  github: ianschuler
  bluesky: ianschuler.bsky.social
  linkedin: ianschuler

---
<Text>
  As CEO, Ian oversees the technology strategy and development capacity at Development Seed, keeping it pointed at the most interesting problems in development.

  Ian graduated from Johns Hopkins University, where he "focused" on physics, economics, computer science, and international relations.
</Text>

```

### Organization of the content

A quick look inside the `content` folder will reveal the different content types:

    .
    ├── blog
    ├── career
    ├── expertise
    ├── project
    ├── team

Each of these folders is organized the same way:

    .
    ├── project
         ├── media
         ├── posts

As you may have guessed, all the `.mdx` files go inside `posts` and all the images go inside `media`.

There are 3 content types with a slightly different structure.

**Projects**

    .
    ├── project
         ├── archived
         ├── media
         ├── posts

The `Project` content type contains an additional folder called `archived`. This is where the Devseed legacy projects `.mdx` files are placed. These projects will not show up on the website but a page is still rendered for them.

**Team**

    .
    ├── team
         ├── archived
         ├── media
         ├── posts

The `Team` content type contains an additional folder called `archived`. This is the where the Devseed alumni `.mdx` files are placed. When someone leaves Development Seed, their team file should be moved to this folder to archive it. Gatsby will take care of the rest.

**Blog**

    .
    ├── blog
         ├── media
         ├── posts
            ├── <year>

In the `Blog` case, inside the `posts` folder we'll find an additional folder with the post year. This is only for organization purposes and has no impact in the blog post.

## 📝  Creating a new piece of content

The filename of a post is very important and must follow a specific format (`<date>-<slug>.mdx`):

    YYYY-MM-DD-the-post-title.md

The `date` should reflect when the post was created.
The `slug` is a user- and SEO-friendly short text used in a URL to identify and describe a resource. It should uniquely identify the post and contain *only letters, numbers, and dashes*. Should be related to the post but it doesn't necessarily need to be the same as the post tile.

The structure of each content piece will depend on the type you are adding. For example, the properties used for a `Team` member are slightly different from the ones used on a `Project`. Everything is explained below, but every file starts with the `frontmatter` before the main content.

The frontmatter must be the first thing in the file and must take the form of valid YAML set between triple-dashed lines. Here is a basic example:

```yaml
---
title: Blogging Like a Hacker
teaser: Creating posts using yaml is the new cool
---

After the Front Matter comes the post content.
```

Between these triple-dashed lines, you can set the values for each of the needed properties.
If you follow the templates, there's no need to get deep into YAML, but [here's a guide](https://rollout.io/blog/yaml-tutorial-everything-you-need-get-started/) to better understand it.

## 🏞 Image guidance

Detailed image guidance can be found in this /how ticket: https://github.com/developmentseed/how/issues/425

> [!IMPORTANT]
> Several content types will use images to display as the page cover or in the card.
> To ensure that the images are displayed with a proper quality it is recommended that they have no less than 1920px on the long side.

**Proportions**
The images used for the cover and the cards (see image below), have a proportion of 2:1. The site build process will automatically cut the images to fit this proportion but the end result may not be what you are expecting.
To avoid a bad framing it is recommended that you cut the image yourself with a 2:1 proportion, still ensuring the long side is over 1920px.

![](./media/card-cover-preview.png)

## 📇 Adding properties to content

Below are listed all the front matter properties for the different content types.
The properties will be used to render the individual post pages but also the cards wherever they appear.

The actual content that's rendered on the page should be added in the content section (after the `---`). To write the content is not enough to use simple markdown. You have to use the MDX layout blocks, which are covered in detail in the [block layout](./BLOCK_LAYOUT.md) documentation.

### Blog

![](./media/ct-blog.png)

```yaml
---
title: New Beginnings
authors:
  - ian-schuler
teaser: But nothing the copy said could convince her

lead: The copy warned the Little Blind Text, that where it came from it would have been rewritten a thousand times and everything that was left
media:
  card:
    url: ../../media/image.png
  cover:
    url: ../../media/image.png
    attribution:
      name: "Development Seed"
      url: https://developmentseed.org
topics:
- Open Data
- Machine Learning
- Satellite Imagery

related:
  - type: project
    post: rural-accessibility
  - type: blog
    post: 2020-12-08-add-flyover-to-any-app-with-mapbox-gl-director
---
See the BLOCK_LAYOUT.md for more information on how to write the content.
```

- **`title`**: The name of the post.

- **`authors`**: The authors of the post. It must be written in slug format so Gatsby can link it to the proper `Team` member. The easiest way to get the correct author slug is to look at the team member's filename. In this case `2020-01-01-ian-schuler.mdx` has a slug of `ian-schuler` - Remove the date and you're left with the slug.

- **`teaser`**: The teaser is a brief description that is show on the blog cards. It should have a maximum of 150 characters.

- **`lead`**: The lead is displayed in the post page with a larger type.

- **`media.card.url`**: The url (relative to the post folder) of the image to use for the card. See [image guidance](#-image-guidance) for size information.

- **`media.cover.url`**: The url (relative to the post folder) of the image to use for the post cover. This is displayed as first thing in the post page. See [image guidance](#-image-guidance) for size information.

- **`media.cover.attribution.name`**: It is good to give credit. Set the author name.

- **`media.cover.attribution.url`**: It is good to give credit. Set the author url.

- **`topics`**: List of topics this posts covers. The topics are used as filters in the Blog hub and displayed in the blog card and page.
The selected topics must come from the following list:
  - Team
  - Data & AI/ML
  - Environment
  - Society
  - Cloud Computing & Infrastructure
  - Geospatial Technology & Products

- **`related`**: It is possible to relate blog posts with projects or other blog posts. They will appear at the end of the page in card format. For each related content you must provide a `type` which can be `blog` or `project`, and a `post` property for which you must provide the post slug. The easiest way to get the correct slug is to look at the content type's filename. For the `Blog` posts the slug is the filename without the `.md` extension. For all other content types remove the date and you're left with the slug.
Example:
```yaml
related:
  - type: project
    post: rural-accessibility
  - type: blog
    post: 2020-12-08-add-flyover-to-any-app-with-mapbox-gl-director
```

### Project

![](./media/ct-project.png)

```yaml
---
title: Neat and tidy project
client:
  name: World Bank
  url: http://www.worldbank.org/

teaser: A project with all the frontmatter tags to show how the final result. How marvelous.

lead: Look at how this project is well structured. If features all the frontmatter elements that can be used in project pages. A collaborative editing model allows government agencies at multiple levels to collaborate in improving the map.

overview: But nothing the copy said could convince her and so it didn’t take long until a few insidious Copy Writers ambushed her, made her drunk with power.
challenge: Even the all-powerful Pointing has no control about the blind texts it is an almost unorthographic life One day however a small line of blind text.
outcome: It actually worked out well. Those officials closest to a road can maintain data around it; everyone else across government can work with the same understanding of the state of the road network.

topics:
- Open Data
- Machine Learning
- Satellite Imagery

public:
  url: https://developmentseed.org/

source:
  title: GitHub
  url: https://github.com/developmentseed/developmentseed.github.com

media:
  card:
    url: ../media/hv-grid-cover.jpg
  cover:
    url: ../media/lai-chou-road-construction-cover.jpg
    attribution:
      name: Development Seed
      url: https://developmentseed.org

related:
  - type: project
    post: rural-accessibility
  - type: blog
    post: 2020-12-08-add-flyover-to-any-app-with-mapbox-gl-director
---
See the BLOCK_LAYOUT.md for more information on how to write the content.
```

- **`title`**: The name of the project.

- **`client.name`**: The name of the client for this project. If it is an internal project use `Development Seed`.

- **`client.url`**: The url for the client's website.

- **`teaser`**: The teaser is a brief description that in the project case is only used for SEO purposes. It should have a maximum of 150 characters.

- **`lead`**: The lead is displayed in the project page with a larger type.

- **`overview`**: Brief description of what the project is about.

- **`challenge`**: Explanation of the main problem this project aims to solve.

- **`outcome`**: The solution that was found for the problem.

- **`topics`**: List of topics this posts covers. The topics are used as filters in the Project hub and displayed in the project page.
The selected topics must come from the following list:
  - Labs
  - Data & AI/ML
  - Environment
  - Society
  - Cloud Computing & Infrastructure
  - Geospatial Technology & Products

- **`public.url`**: If an instance of the project is hosted and available somewhere link it here.

- **`source.title`**: Label for the source name. If it is a GitHub repository, just use `GitHub`.

- **`source.url`**: If the project is open-source provide a link where the source can be found.

- **`media.card.url`**: The url (relative to the post folder) of the image to use for the card. See [image guidance](#-image-guidance) for size information.

- **`media.cover.url`**: The url (relative to the post folder) of the image to use for the project cover. This is displayed as first thing in the project page. See [image guidance](#-image-guidance) for size information.

- **`media.cover.attribution.name`**: It is good to give credit. Set the author name.

- **`media.cover.attribution.url`**: It is good to give credit. Set the author url.

- **`related`**: It is possible to relate projects with other projects or blog posts. They will appear at the end of the page in card format. For each related content you must provide a `type` which can be `blog` or `project`, and a `post` property for which you must provide the post slug. The easiest way to get the correct slug is to look at the content type's filename. For the `Blog` posts the slug is the filename without the `.mdx` extension. For all other content types remove the date and you're left with the slug.

Example:
```yaml
related:
  - type: project
    post: rural-accessibility
  - type: blog
    post: 2020-12-08-add-flyover-to-any-app-with-mapbox-gl-director
```

### Expertise

![](./media/ct-expertise.png)

```yaml
---
title: Cloud Geo
teaser: Accelerated and accessible earth science and geospatial analysis.
lead: Equip your scientists, analysts and decision makers to work smarter, faster, and at planetary scale on the cloud.

media:
  card:
    url: ../media/expertise-cloud-geo--cover.jpg
  cover:
    url: ../media/expertise-cloud-geo--cover.jpg
    attribution:
      name: Development Seed
      url: https://developmentseed.org

contentSection:
  subtitle: Why it matters
  title: Cloud technologies are changing how we understand the earth and share that understanding with others.
  lead: We remove the complexity of managing planetary scale data in rapidly changing cloud environments.
---
See the BLOCK_LAYOUT.md for more information on how to write the content.
```

- **`title`**: The name of the expertise.

- **`teaser`**: The teaser is a brief description that is show on the expertise cards. It should have a maximum of 150 characters.

- **`lead`**: The lead is displayed in the expertise page with a larger type.

- **`media.card.url`**: The url (relative to the post folder) of the image to use for the card. See [image guidance](#-image-guidance) for size information.

- **`media.cover.url`**: The url (relative to the post folder) of the image to use for the expertise cover. This is displayed as first thing in the expertise page. See [image guidance](#-image-guidance) for size information.

- **`media.cover.attribution.name`**: It is good to give credit. Set the author name.

- **`media.cover.attribution.url`**: It is good to give credit. Set the author url.

- **`contentSection`**: The content section of each expertise starts with outlining what the expertise is about.

- **`contentSection.subtitle`**: Subtitle for the content section.

- **`contentSection.title`**: Title for the expertise content section. Should work as a call to action to the content.

- **`contentSection.lead`**: Brief introduction for the content that follows.

### Team member

![](./media/ct-team.png)

```yaml
---
title: Ian Schuler
expertise: CEO
group: biz-op

teaser: Ian oversees our strategy and team to make sure we are doing meaningful, impactful work.

location: Washington DC, USA
pronouns: he/him

media:
  avatar:
    url: ../media/schuler.thumb.jpg
  card:
    url: ../media/schuler.jpg
social:
  github: ianschuler
  bluesky: ianschuler.bsky.social
  linkedin: ianschuler
  website: http://example.com
---
See the BLOCK_LAYOUT.md for more information on how to write the content.
```

- **`title`**: The name of the team member.

- **`expertise`**: The expertise or role of this person in the company. (Example: Designer, Finance, etc.)

- **`group`**: The group or team this person belongs to. This is used to group people on the Team page. Should be one of:

  ```
    biz-op       ->  Business Strategy & Operations
    engineering  ->  Engineering
    data         ->  Data
    design-dev   ->  Design & Development
  ```

- **`teaser`**: The teaser is a brief description that is show on the team cards. It should have a maximum of 150 characters.

- **`location`**: Where is the team member based. Use `City, Country`, or `City, State, Country`.

- **`pronouns`**: If a person so wishes, they can list their preferred pronouns.

- **`media.avatar.url`**: The url (relative to the post folder) of the person's thumbnail. This is used when referencing blog content created by this person.

- **`media.card.url`**: The url (relative to the post folder) of the image to use for the card and on the team member's page. See [image guidance](#-image-guidance) for size information.

- **`social`**: The different usernames used in the social networks. Currently supported:

  ```
  github
  bluesky
  linkedin
  website
  ```

### Career

![](./media/ct-career.png)

```yaml
---
title: General Application
teaser: Don’t see something that fits your skillset right now? Submit a general application anyway. We are always eager to connect with people who would be a great fit for the team.
lead: Take DevSeed to the next level of global impact.
location: Global
application:
  url: https://example.com/job-offer
---
See the BLOCK_LAYOUT.md for more information on how to write the content.
```

- **`title`**: The name of the position.

- **`teaser`**: The teaser is a brief description that is show on the career list.

- **`lead`**: The lead is displayed in the career page with a larger type.

- **`location`**: If this career is for a specific location it should be stated with this property. `Global` is also an option if there's no geographic restriction.

- **`application`**: Data for the job application form.

- **`application.url`**: External url for the application form

### Event

The Event content type is used to populate a table of events that our team members will attend, while providing information of the talks they will give.
Each event file will render a row of the table.

![Table of events](./media/events-table.png)

```yaml
---
title: State of the Map 2023
location: Richmond (USA)
eventDate:
  - 2023-06-08
  - 2023-06-11
url: https://2023.stateofthemap.us/
blogPost: 2020-12-08-add-flyover-to-any-app-with-mapbox-gl-director
schedule:
  - title: Simplifying access to OpenStreetMap data for urban planning
    participant: vitor-george
  - title: The state of OSMCha
    participant: wille-marcel
  - title: Some other talk name
    participant:
      - kiri-carini
      - kathryn-berger
---
The Event content type has no content section.
```

- **`title`**: The name of the event.

- **`location`**: Where the event is happening.

- **`eventDate`**: Start and End date of the event. If the event is a single day, use only one date, but it should always be a list.
Example:
```yaml
  eventDate:
    - 2023-06-01
```

- **`url`**: Url to the event's website.

- **`blogPost`**: Blog post slug if there's a blog post that should be feature on this event. The easiest way to get the correct slug is to look at the content type's filename. For the `Blog` posts the slug is the filename without the `.md` extension.

- **`schedule`**: List of people and their respective talks. The `title` is the name of the talk and the `participant` is the slug of the team member. The easiest way to get the correct slug is to look at the team member's filename. In this case `2020-01-01-ian-schuler.mdx` has a slug of `ian-schuler` - Remove the date and you're left with the slug.

- **`schedule[].title`**: The name of the talk(s).

- **`schedule[].participant`**: The slug of the team member(s) giving the talk.

Example:
```yaml
schedule:
  - title: Simplifying access to OpenStreetMap data for urban planning
    participant: vitor-george
  - title: The state of OSMCha
    participant: wille-marcel
```

If there's more than one person giving the talk, or more than one talk by the same people, the `title` and `participant` should be lists. Example:
```yaml
schedule:
  - title:
      - The Snow White of GIS
      - How to decide between a cone or a cup
    participant:
      - kiri-carini
      - kathryn-berger
```
