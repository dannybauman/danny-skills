<h1 align="center">
  DS.O V5 - <small>Block layout</small>
</h1>

> [!TIP]
> Check the [templates](./TEMPLATES.md) for bootstrap content pieces.


- [📚 Block layout](#-block-layout)
- [🧱 Block types](#-block-types)
  - [Text](#text)
  - [Pull quote](#pull-quote)
  - [Feature list](#feature-list)
  - [Number list](#number-list)
  - [Diptych](#diptych)
  - [Media - Image](#media---image)
    - [Cover](#cover)
    - [Large](#large)
    - [Default](#default)
  - [Media - Video](#media---video)
  - [Browser Media](#browser-media)

## 📚 Block layout

Using simple [Markdown](https://www.markdownguide.org/) content in a post allows for quick content creation, however a richer layout will be more engaging and interesting for the user.
To achieve this, the Devseed website uses the concept of a **block layout** to create content pages. This layout system allows you to pick, from a pool of content block types, the one that better suits the content at hand.

For example, these two pages have the same content. The one on the left uses simple markdown and on the right the block layout.

![Layout block example](./media/bl-compare.png)

## 🧱 Block types

There are several types of block, each one with different properties and customization options, but they are all defined in the same way.

A block is defined by a tag and may have a set of attributes. The tag is the name of the block and is inclosed in angle brackets (`<` and `>`).
Most block tags come in pairs, consisting of an opening tag and a closing tag. The opening tag marks the beginning of the block, while the closing tag, which includes a forward slash before the tag name, indicates the end of that block. Each tag created a different block by displaying the contents enclosed by it accordingly.

The simplest example, with an opening and closing tag, is the `Text` block.
```jsx
<Text>
  This is a *text block*.
</Text>
```

The content of any block can be written in markdown format, like the example above.

Some of the blocks have attributes which are used to provide additional information to the block. All the attributes are defined within the opening tag in a key-value pair format (`key="value"`).
```jsx
<Media size="large">
  Image caption
</Media>
```

There is only one exception to the `key="value"` format which is the `src` property of any block that displays media. Because of how images are processed by the framework, this property must be defined as:
```jsx
src={require("local-image-url.png")}
```

Although, most of the times, there is an opening tag and a closing tag, it's not always the case. When a block has non content is becomes a self-closing tag.
```jsx
<Media size="large" src={require("local-image-url.png")} />
```
> [!TIP]
> To increase the content readability, you can add line breaks in between the block attributes. For example:
> ```jsx
> <Media
>  size="large"
>  src={require("local-image-url.png")}
> />
> ```


### Text

![Text block](./media/bl-text.png)

```jsx
<Text>
  The **Big Oxmox** advised her not to do so, because there were thousands
  of bad Commas, wild [Question Marks](http://example.com) and devious
  Semikoli, but the Little Blind Text didn’t listen. She packed her seven
  versalia, put her initial into the belt and _made herself on the way_.
</Text>
```

The `text` block is perhaps the simplest one and allows you to render text on a page. _Markdown supported._

### Pull quote

![Pull quote block](./media/bl-pull-quote.png)

```jsx
<PullQuote>
  <PullQuote.Quote>
    But nothing the copy said could convince her
  </PullQuote.Quote>
  <PullQuote.Content>
    ### Little Blind Text

    The copy warned the Little Blind Text, that where it came from it would have
    been rewritten a thousand times and everything that was left from its origin
    would be the word "and" and the Little Blind Text should turn around and return
    to its own, safe country.
  </PullQuote.Content>
</PullQuote>
```

The `pull-quote` block allows you to render a text block with an highlight on the right side. This highlight should be kept relatively short to remain balanced with the rest of the text.

> [!NOTE]
> Because the `pull-quote` block has two parts, the `quote` and the `content`, it requires a more complex structure with nested tags.

- **`<PullQuote>`** - The main tag which should wrap the whole block.
- **`<PullQuote.Quote>`** - _Markdown supported._ The quote to highlight.
- **`<PullQuote.Content>`** - _Markdown supported._ The content of the block.

### Feature list

![Feature list block](./media/bl-feature-list.png)

```jsx
<FeatureList>
  <FeatureList.Item
    title="On deer horse"
    src={require("../media/image.jpg")}
    attributionName="Development Seed"
    attributionUrl="https://developmentseed.org"
  >
    The Big Oxmox advised her not to do so, because there were thousands of bad Commas, wild Question Marks and devious Semikoli.
  </FeatureList.Item>
  <FeatureList.Item
    title="Overlaid the jeepers"
    src={require("../media/image.jpg")}
  >
    It is a paradisematic country, in which roasted parts of sentences fly into your mouth.
  </FeatureList.Item>
  <FeatureList.Item title="The copy warned the Little Blind Text" >
    The word _and_ and the Little Blind Text **should** turn around and return to its own, safe country.
  </FeatureList.Item>
</FeatureList>
```

The `feature-list` can be used to display a list of items in 2 columns. Each of the items can have an `image`, `title` and `content`, even though none of these properties are required thus giving the author creative freedom.

- **`<FeatureList>`** - The main tag which should wrap the whole block.
- **`<FeatureList.Item>`** - Each item in the list with the following attributes:
  - **`title`**: Title for the list item.
  - **`src`**: The url (relative to the post folder) of the image to use in the item. **Must be defined as `src={require("local-image-url.png")}`.**
  - **`attributionName`**: It is good to give credit. Set the author name.
  - **`attributionUrl`**: It is good to give credit. Set the author url.
  - **`block content`**: _Markdown supported._ A short description for the list item.

### Number list

![Number list block](./media/bl-number-list.png)

```jsx
<NumberList>
  <NumberList.Item
    title="On deer horse"
    value="30"
    unit="km"
  >
    The word _and_ and the Little Blind Text **should** turn around and return to its own, safe country.
  </NumberList.Item>
  <NumberList.Item
    title="Turn around and return"
    value="7"
    unit="years"
  >
    The Big Oxmox advised her not to do so, because there were **thousands of bad Commas**.
  </NumberList.Item>
  <NumberList.Item title="Bedtime stories" value="23"/>
  <NumberList.Item value="42">
    Should be the answer to life the universe and everything.
  </NumberList.Item>
</NumberList>
```

The `number-list` can be used to display a list of big number in 2 columns. To each number can be associated a `unit`, a `title`, and a brief description though `content`, even though the only property really required is the value, giving the author creative freedom.

- **`<NumberList>`** - The main tag which should wrap the whole block.
- **`<NumberList.Item>`** - Each item in the list with the following attributes:
  - **`title`**: Title for the list item.
  - **`value`**: The big number to show.
  - **`unit`**: The unit associated to the number.
  - **`block content`**: _Markdown supported._ A short description for the list item.

### Diptych

_A diptych is an artwork consisting of two pieces or panels, that together create a singular art piece these can be attached together or presented adjoining each other._

![Diptych block](./media/bl-diptych.png)

```jsx
<Diptych>
  <Diptych.Media src={require("../media/image.jpg")} alt="Image alt text" />
  <Diptych.Content>
    ## Copy Writers ambushed her

    The Big Oxmox advised her not to do so, because there were [thousands of bad Commas](http://example.com), wild Question Marks and devious **Semikoli**, but the Little Blind Text didn’t listen.
  </Diptych.Content>
</Diptych>
```

The `diptych` block is used to display a block of text and an image side by side. The image can be on the left or right side of the text, and this is controlled by the order of the tags. (`<Diptych.Media>` and `<Diptych.Content>`)

- **`<Diptych>`** - The main tag which should wrap the whole block.
- **`<Diptych.Media>`** - The media tag with the following attributes:
  - **`src`**: The url (relative to the post folder) of the image to use in the item. **Must be defined as `src={require("local-image-url.png")}`.**
  - **`alt`**: The media alt text.
- **`<Diptych.Content>`** - _Markdown supported._ The content of the block.

> [!TIP]
> You can use `<Diptych.BrowserMedia>` instead of `<Diptych.Media>` to render a frame around the content. See [Browser Media](#browser-media) for details on props.

### Media - Image

When used with an image, the `Media` block can be displayed in 3 different sizes (`cover`, `large`, or `default`), and some of the properties used depend on the chosen size.

#### Cover

![Cover image block](./media/bl-img-cover.png)

A cover image will span the full width of the page and can have a decoration (no decoration is also an option) on the top or bottom of the right side.

```jsx
<Media
  size="cover"
  src={require("../media/image.jpg")}
  decoration="top"
  attributionName="Development Seed"
  attributionUrl="https://developmentseed.org"
>
  Using markdown in a caption body is **not recommended** but it is possible. Observe the bold and [this link](https://developmentseed.org)!
</Media>
```

- **`size`**: The size of the image block. `cover` in this case.
- **`src`**: The url (relative to the post folder) of the image to use in the item. **Must be defined as `src={require("local-image-url.png")}`.**
- **`decoration`**: Where and if to show the decoration. Can be `top`, `bottom`, or `none` for an image block of `cover` size.
- **`attributionName`**: It is good to give credit. Set the author name.
- **`attributionUrl`**: It is good to give credit. Set the author url.
- **`block content`**: _Markdown supported._ Caption to display below the image.

#### Large

![Large image block](./media/bl-img-large.png)

A large image will overflow the width of the text body. Can have a decoration (no decoration is also an option) on the left or right side.

```jsx
<Media
  size="cover"
  src={require("../media/image.jpg")}
  decoration="left"
  attributionName="Development Seed"
  attributionUrl="https://developmentseed.org"
>
  Using markdown in a caption body is **not recommended** but it is possible. Observe the bold and [this link](https://developmentseed.org)!
</Media>
```

- **`size`**: The size of the image block. `large` in this case.
- **`src`**: The url (relative to the post folder) of the image to use in the item. **Must be defined as `src={require("local-image-url.png")}`.**
- **`decoration`**: Where and if to show the decoration. Can be `right`, `left`, or `none` for an image block of `large` size.
- **`attributionName`**: It is good to give credit. Set the author name.
- **`attributionUrl`**: It is good to give credit. Set the author url.
- **`block content`**: _Markdown supported._ Caption to display below the image.

#### Default

![Default image block](./media/bl-img-default.png)

A default image will maintain its original size while fitting within the text body. It has no decoration element.

```jsx
<Media
  size="cover"
  src={require("../media/image.jpg")}
  attributionName="Development Seed"
  attributionUrl="https://developmentseed.org"
>
  Using markdown in a caption body is **not recommended** but it is possible. Observe the bold and [this link](https://developmentseed.org)!
</Media>
```

- **`size`**: The size of the image block. `default` in this case. Not specifying the size will default to `default`.
- **`src`**: The url (relative to the post folder) of the image to use in the item. **Must be defined as `src={require("local-image-url.png")}`.**
- **`attributionName`**: It is good to give credit. Set the author name.
- **`attributionUrl`**: It is good to give credit. Set the author url.
- **`block content`**: _Markdown supported._ Caption to display below the image.

### Media - Video

> [!IMPORTANT]
> the only supported video formats are either `mp4` or `webm`.

A `Media` block will be rendered as a video player when the file extension is `.mp4` or `.webm`.

This block can be displayed in 2 different sizes (`large`, or `default`). All the properties are the same regardless of size.
A large video will overflow the width of the text body. A default video will maintain its original size while fitting within the text body.

```jsx
<Media
  size="default"
  src={require("../media/video.mp4")}
  attributionName="Development Seed"
  attributionUrl="https://developmentseed.org"
>
  Using markdown in a caption body is **not recommended** but it is possible. Observe the bold and [this link](https://developmentseed.org)!
</Media>
```

- **`size`**: The size of the video block. Can be `large` or `default`.
- **`src`**: The url (relative to the post folder) of the video to use. **Must be defined as `src={require("local-video-url.mp4")}`.**
- **`attributionName`**: It is good to give credit. Set the author name.
- **`attributionUrl`**: It is good to give credit. Set the author url.
- **`block content`**: _Markdown supported._ Caption to display below the video.

### Browser Media

![Browser media block](./media/bl-browser-media.png)

The `BrowserMedia` block is used to display a browser window frame around an image or video. This block can be used to show a screenshot of a website or a video of a website in action.

```jsx
<BrowserMedia
  size="large"
  src={require("../media/image.jpg")}
  alt="Video of the Co2ordinate webapp"
  title="Co2ordinate"
  url="https://developmentseed.org/co2ordinate"
  noShadow
  noColor
>
  Using markdown in a caption body is **not recommended** but it is possible. Observe the bold and [this link](https://developmentseed.org)!
</BrowserMedia>
```

- **`size`**: The size of the media block. Can be `large`, `cover` or `default`.
- **`src`**: The url (relative to the post folder) of the media to use in the item. **Must be defined as `src={require("local-image-url.png")}`.**
- **`alt`**: The media alt text.
- **`title`**: The title of the website which is displayed on the top bar of the browser frame.
- **`url`**: An optional url to link to when the user clicks on top right icon.
- **`noShadow`**: If set, the browser frame will not have a shadow.
- **`noColor`**: If set, the browser frame action dots will not have a color.
- **`block content`**: _Markdown supported._ Caption to display below the browser frame.

> [!TIP]
> The `BrowserMedia` block is a special block and can be nested inside the `Text` or `PullQuote.Content` blocks.
