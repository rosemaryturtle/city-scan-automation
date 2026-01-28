# OJS Chart Integration

### Prerequisites


To use the OJS charting capabilities in your Quarto document, ensure you have the following prerequisites:

- Have a **processed** folder under **02-process-outputs/tabular**, if not, you *could* create using [R/clean-tabular.R](R/clean-tabular.R)

- At the beginning of the qmd file, include:

```javascript
d3 = require("d3@7")

import { setD3, setWidth, setCity, setCountry, plot_pga, plot_pgp, plot_pas, ... , plot_fwi, plot_fwi_d } from "./ojs/plots.js"

setD3(d3)
setWidth(width)               // width of the plot
setCity("Nouakchott")         // for the subtitle, can read off the city variable in the quarto doc.
setCountry("Mauritania")
setHeightRatio(1.25)          // height ratio to width

import { loadData } from "./ojs/dataloader.js"
d = loadData()
```

The [ojs](./ojs) folder contains the necessary JavaScript files for plotting and data loading. Dataloader reads the processed tabular data from *02-process-outputs/tabular/processed*. 

he loadData() function returns an object d containing all the datasets. The data names match Caroline's Observable notebook naming convention, so plots can be called the same way:

```javascript
plot_pga(d.pg)       // Population growth (absolute)
plot_pas(d.pas)      // Population age structure
plot_fwi(d.fwi)      // Fire weather index
```

for reference, refer to https://github.com.mcas.ms/carolinecullinan/nouakchott-mauritania and https://observablehq.com/@carolinecullinan/nouakchott-scanned


to publish to Quarto Pub, it needs to include the processed data files. Add them to _quarto.yml:
```
project:
  type: website
  render:
    - index.qmd
  resources:
    - 02-process-output/tabular/processed/*
```