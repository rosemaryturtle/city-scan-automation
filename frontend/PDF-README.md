# PDF README

*_post-render.R generates the PDF.*

We are using [Vivliostyle](https://vivliostyle.org) to save the City Scan to PDF. This allows us to use CSS to style a PDF, enabling us to use the same styles as the interactive version (when desired).

## Sass → CSS
Right now we are using `source/custom.scss` as our style sheet for both the HTML version and the print version. We might want to separate this, instead of simply relying on a media query. Regardless, that style sheet is a [Sass](https://sass-lang.com) stylesheet (see that it ends `.scss` instead of `.css`), which makes writing CSS easier, but which Vivliostyle can't read. We therefore need to convert from Sass to CSS:

```
$ sass source/custom.scss source/custom.scss
```

If we are continuing to edit custom.scss we can watch for changes so that custom.css gets automatically updated.

```
$ sass --watch source/custom.scss source/custom.scss
```

## Linking the stylesheet

We could generate the PDF from the HTML of the City Scan or from a markdown file generated by Quarto. For now, we will use the HTML so that the document structure is more similar, only relying on one converter. As it is currently set up, the HTML output relies on 4 style sheets:

1. `<link href="index_files/libs/quarto-html/tippy.css" rel="stylesheet">`
2. `<link href="index_files/libs/quarto-html/quarto-syntax-highlighting.css" rel="stylesheet" id="quarto-text-highlighting-styles"> `
3. `<link href="index_files/libs/bootstrap/bootstrap-icons.css" rel="stylesheet">`
4. `<link href="index_files/libs/bootstrap/bootstrap.min.css" rel="stylesheet" id="quarto-bootstrap" data-mode="light">`

The final one includes the styles from custom.scss. However, we would like to override all of these. So, before rendering the PDF we want to delete/comment out each of these lines and add in our desired stylesheet:
We want to override these

```
<link href="source/custom.css" rel="stylesheet">
```

## Generating PDF

We can build the PDF or we can generate a preview:

```
$ vivliostyle build index.html
$ vivliostyle preview index.html
```