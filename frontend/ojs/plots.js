// plots.js - Plotting functions from Caroline's Observable notebook
// Source: https://observablehq.com/@carolinecullinan/nouakchott-scanned

let d3;
let plotWidth = 800;
let heightRatio = 0.6;
let globalCity = "City";
let globalCountry = "Country";

// Call this first with d3 from OJS: setD3(require("d3@7"))
export function setD3(d3Instance) {
  d3 = d3Instance;
}

// Set plot width - call with Observable's width: setWidth(width)
export function setWidth(w) {
  plotWidth = w;
}

// Set height ratio (default 0.6 = 60% of width)
export function setHeightRatio(r) {
  heightRatio = r;
}

// Set city and country names
export function setCity(name) {
  globalCity = name;
}

export function setCountry(name) {
  globalCountry = name;
}

// ------------------------------------------------------------
// wrapText
// ------------------------------------------------------------
function wrapText(text, maxWidth, font) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  context.font = font;
  
  const words = text.split(" ");
  const lines = [];
  let currentLine = "";
  
  words.forEach(word => {
    const testLine = currentLine + (currentLine ? " " : "") + word;
    const metrics = context.measureText(testLine);
    
    if (metrics.width > maxWidth && currentLine) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = testLine;
    }
  });
  
  if (currentLine) {
    lines.push(currentLine);
  }
  
  return lines;
}


// ------------------------------------------------------------
// calculateAgeDependencyRatios
// ------------------------------------------------------------
function calculateAgeDependencyRatios(pas) {
    // aggregate data into age groups: young (under 15 years); working age (15-64 years); and elderly (65 + years)
    const ageGroups = {
      youth: ["0-4", "5-9", "10-14"],
      workingAge: ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64"],
      elderly: ["65-69", "70-74", "75-79", "80+"]
    };
    
    // calculate totals for each age group
    const youthTotal = d3.sum(pas.filter(d => ageGroups.youth.includes(d.ageBracket)), d => d.count);
    const workingAgeTotal = d3.sum(pas.filter(d => ageGroups.workingAge.includes(d.ageBracket)), d => d.count);
    const elderlyTotal = d3.sum(pas.filter(d => ageGroups.elderly.includes(d.ageBracket)), d => d.count);
    
    // calculate dependency ratios
    const youthDependencyRatio = (youthTotal / workingAgeTotal) * 100;
    const elderlyDependencyRatio = (elderlyTotal / workingAgeTotal) * 100;
    const totalDependencyRatio = youthDependencyRatio + elderlyDependencyRatio;
    
    return {
      youthDependencyRatio: Math.round(youthDependencyRatio),
      elderlyDependencyRatio: Math.round(elderlyDependencyRatio), 
      totalDependencyRatio: Math.round(totalDependencyRatio),
      youthTotal,
      workingAgeTotal,
      elderlyTotal
    };
  }


// ------------------------------------------------------------
// parseRwiCategory
// ------------------------------------------------------------
function parseRwiCategory(bin) {
    const categoryOrder = {
      "Least wealthy": 1,
      "Less wealthy": 2,
      "Average wealth": 3,
      "More wealthy": 4,
      "Most wealthy": 5
    };
    
    return categoryOrder[bin] || 0;
  }


// ------------------------------------------------------------
// parseUbaAreaRange
// ------------------------------------------------------------
function parseUbaAreaRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('Before')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parsePvAreaRange
// ------------------------------------------------------------
function parsePvAreaRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseAirQualityRange
// ------------------------------------------------------------
function parseAirQualityRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseSummerRange
// ------------------------------------------------------------
function parseSummerRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseNdviRange
// ------------------------------------------------------------
function parseNdviRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseElevationRange
// ------------------------------------------------------------
function parseElevationRange(bin) {
    const binStr = String(bin);
    
    if (binStr.startsWith('-')) {
      return parseFloat(binStr);
    }
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    if (binStr.includes('+')) {
      return parseFloat(binStr.replace('+', ''));
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseSlopeRange
// ------------------------------------------------------------
function parseSlopeRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseLsAreaRange
// ------------------------------------------------------------
function parseLsAreaRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// parseLAreaRange
// ------------------------------------------------------------
function parseLAreaRange(bin) {
    const binStr = String(bin);
    
    if (binStr.includes('-')) {
      const [start] = binStr.split('-').map(x => parseFloat(x));
      return start;
    }
    
    return parseFloat(binStr);
  }


// ------------------------------------------------------------
// plot_pga
// ------------------------------------------------------------
function plot_pga(pg, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Population",
  xLabel = "Year",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range for title
  const minYear = d3.min(pg, d => d.yearName);
  const maxYear = d3.max(pg, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain(d3.extent(pg, d => d.yearName))
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...pg.map(d => d.population)) * 1.1])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d => {
      if (d === 0) return "0";
      if (d >= 1000000) return `${(d/1000000).toFixed(d % 1000000 === 0 ? 0 : 1)}M`;
      if (d >= 1000) return `${(d/1000).toFixed(0)}K`;
      return d;
    });

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    // .attr("dx", "-0.3em"); // label positioning slightly left
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d3.format("d"))
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em"); // label positioning slightly down
  
  // line
  const line = d3.line()
    .x(d => xScale(d.yearName))
    .y(d => yScale(d.population));
    
  g.append("path")
    .datum(pg)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // dots
  g.selectAll(".dot")
    .data(pg)
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.yearName))
    .attr("cy", d => yScale(d.population))
    .attr("r", Math.max(2, Math.min(3, width / 200)))
    .attr("fill", "black")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>Population: ${d.population.toLocaleString()}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Population Growth, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);
    
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_pgp
// ------------------------------------------------------------
function plot_pgp(pg, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Population Growth Percentage",
  xLabel = "Year",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range for title
  const minYear = d3.min(pg, d => d.yearName);
  const maxYear = d3.max(pg, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain(d3.extent(pg, d => d.yearName))
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...pg.map(d => d.populationGrowthPercentage)) * 1.1])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d => d);

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    // .attr("dx", "-0.3em"); // label positioning slightly left
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d3.format("d"))
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em"); // label positioning slightly down
  
  // line (with defined function to skip null values)
  const line = d3.line()
    .defined(d => d.populationGrowthPercentage !== null)
    .x(d => xScale(d.yearName))
    .y(d => yScale(d.populationGrowthPercentage));
    
  g.append("path")
    .datum(pg)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // dots (filter out null values)
  g.selectAll(".dot")
    .data(pg.filter(d => d.populationGrowthPercentage !== null))
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.yearName))
    .attr("cy", d => yScale(d.populationGrowthPercentage))
    .attr("r", Math.max(2, Math.min(3, width / 200)))
    .attr("fill", "black")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>Growth Percentage: ${d.populationGrowthPercentage !== null ? d.populationGrowthPercentage.toFixed(2) + '%' : 'N/A'}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Population Growth Percentage, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel + " (%)");
    
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_pas
// ------------------------------------------------------------
function plot_pas(pas, {
    cityName = globalCity,
    width = plotWidth,
    yLabel = "Percentage of Age Distribution",
    xLabel = "Age Bracket",
    color = "black"
  } = {}) {
    
    // get year for title
    const year = d3.max(pas, d => d.yearName);
    
    // define age bracket order
    const ageBrackets = [
      "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", 
      "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", 
      "65-69", "70-74", "75-79", "80+"
    ];
    
    // set up dimensions with dynamic sizing
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(10, width * 0.01),
      bottom: Math.max(90, width * 0.05),
      left: Math.max(40, width * 0.04)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // scales
    const xScale = d3.scaleBand()
      .domain(ageBrackets)
      .range([0, innerWidth])
      .paddingInner(0.3)
      .paddingOuter(1.3);
      
    // sub-scales for grouping female/male bars
    const xSubScale = d3.scaleBand()
      .domain(["female", "male"])
      .range([0, xScale.bandwidth()])
      .padding(0.1);
    
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(...pas.map(d => d.percentage)) * 1.5])
      .range([innerHeight, 0]);
    
    // color scale
    const colorScale = d3.scaleOrdinal()
      .domain(["female", "male"])
      .range(["#f05f5c", "#00b4b7"]);
    
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10px system-ui"); // Observable Plot default styling to match other plots
      
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines
    const yTicks = Math.max(4, Math.min(8, Math.floor(width / 100)));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(${xScale.bandwidth() / 4},${innerHeight})`); // x-axis label offset so that the x-axis label text appears centered between the female and male bars of each x-axis age group bin    
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", ".15em")
      .attr("transform", "rotate(-45)");
    
    // baseline rule
    g.append("line")
      .attr("x1", 0)
      .attr("x2", innerWidth)
      .attr("y1", yScale(0))
      .attr("y2", yScale(0))
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    
    // data bars
    g.selectAll(".bar")
      .data(pas)
      .enter().append("rect")
      .attr("class", "bar")
      .attr("x", d => xScale(d.ageBracket) + xSubScale(d.sex))
      .attr("width", xSubScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => colorScale(d.sex))
      .style("cursor", "default");
    
    // invisible hover areas for tooltips
    ageBrackets.forEach(bracket => {
      const femaleData = pas.find(d => d.ageBracket === bracket && d.sex === "female");
      const maleData = pas.find(d => d.ageBracket === bracket && d.sex === "male");
      
      g.append("rect")
        .attr("class", "hover-area")
        .attr("x", xScale(bracket))
        .attr("width", xScale.bandwidth())
        .attr("y", 0)
        .attr("height", innerHeight)
        .attr("fill", "transparent")
        .style("cursor", "default")
        .on("mouseover", function(event) {
          // remove any existing tooltips
          d3.selectAll(".d3-tooltip").remove();
          
          // tooltip
          const tooltip = d3.select("body").append("div")
            .attr("class", "d3-tooltip")
            .style("position", "absolute")
            .style("background", "white")
            .style("color", "black")
            .style("padding", "12px 16px")
            .style("border", "1px solid #000000")
            .style("font-family", "system-ui")
            .style("font-size", "12px")
            .style("font-weight", "normal")
            .style("line-height", "1.4")
            .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
            .style("pointer-events", "none")
            .style("z-index", "1000")
            .style("opacity", 0);
          
          const tooltipContent = `
            <div style="font-weight: bold; margin-bottom: 8px;">Age Bracket: ${bracket}</div>
            <div style="border-bottom: 1px solid #ddd; margin-bottom: 6px;"></div>
            <div style="margin-bottom: 4px;">Female: ${femaleData?.percentage.toFixed(2) || '0.00'}% (${femaleData?.count.toFixed(0) || '0'} females)</div>
            <div style="">Male: ${maleData?.percentage.toFixed(2) || '0.00'}% (${maleData?.count.toFixed(0) || '0'} males)</div>
          `;
          
          tooltip.html(tooltipContent)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")
            .transition()
            .duration(200)
            .style("opacity", 1);
        })
        .on("mousemove", function(event) {
          const tooltip = d3.select(".d3-tooltip");
          if (!tooltip.empty()) {
            tooltip
              .style("left", (event.pageX + 10) + "px")
              .style("top", (event.pageY - 10) + "px");
          }
        })
        .on("mouseout", function() {
          d3.selectAll(".d3-tooltip")
            .transition()
            .duration(200)
            .style("opacity", 0)
            .remove();
        });
    });
    
    // legend
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);
    
    const legendData = [
      { sex: "female", color: "#f05f5c", label: "female" },
      { sex: "male", color: "#00b4b7", label: "male" }
    ];
    
    const legendItems = legend.selectAll(".legend-item")
      .data(legendData)
      .enter().append("g")
      .attr("class", "legend-item")
      .attr("transform", (d, i) => `translate(${i * 80}, 0)`);
    
    legendItems.append("rect")
      .attr("width", 12)
      .attr("height", 12)
      .attr("fill", d => d.color);
      
    legendItems.append("text")
      .attr("x", 18)
      .attr("y", 6)
      .attr("dy", "0.35em")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(d => d.label);
    
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`Population Distribution by Age and Sex, ${year}`);
    
    // subtitle
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(cityName);
    
    // y-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight / 2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(yLabel + " (%)");

     // x-axis label
     svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 15)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(xLabel);
    
    return svg.node();
  }


// ------------------------------------------------------------
// plot_pas_pyramid
// ------------------------------------------------------------
function plot_pas_pyramid(pas, {
    cityName = globalCity,
    width = plotWidth,
    yLabel = "Age Bracket",
    xLabel = "Percentage of Age Distribution",
    color = "black"
  } = {}) {
    
    // get year for title
    const year = d3.max(pas, d => d.yearName);
    
    // age bracket order (bottom (youngest) to top (oldest) for pyramid)
    const ageBrackets = [
      "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", 
      "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", 
      "65-69", "70-74", "75-79", "80+"
    ].reverse(); // reverse for pyramid (oldest at top)
    
    // set up dimensions
    const height = width * 0.8; // taller for pyramid
    const margin = {
      top: 70,
      right: Math.max(60, width * 0.06), // more space for percentage labels
      bottom: Math.max(90, width * 0.04),
      left: Math.max(60, width * 0.06)  // more space for percentage labels
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // max percentage for symmetric scale
    const maxPercentage = d3.max(pas, d => d.percentage);
    
    // scales
    const yScale = d3.scaleBand()
      .domain(ageBrackets)
      .range([0, innerHeight])
      .paddingInner(0.1)
      .paddingOuter(0.1);
      
    // x scale for percentages (0 to max, mirrored for males)
    const xScale = d3.scaleLinear()
      .domain([0, maxPercentage * 1.1]) // add padding
      .range([0, innerWidth / 2]);
    
    // color scale
    const colorScale = d3.scaleOrdinal()
      .domain(["female", "male"])
      .range(["#f05f5c", "#00b4b7"]);
    
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10px system-ui");
      
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // center line
    g.append("line")
      .attr("x1", innerWidth / 2)
      .attr("x2", innerWidth / 2)
      .attr("y1", 0)
      .attr("y2", innerHeight)
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    
    // y-axis on the left showing age groups
    const yAxis = g.append("g")
      .attr("class", "y-axis")
      .attr("transform", `translate(0, 0)`);
      
    yAxis.call(d3.axisLeft(yScale)
      .tickSize(0)
      .tickPadding(10))
      .select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
      
    yAxis.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
    
    // male bars (left side)
    const maleData = pas.filter(d => d.sex === "male");
    g.selectAll(".male-bar")
      .data(maleData)
      .enter().append("rect")
      .attr("class", "male-bar")
      .attr("x", d => innerWidth / 2 - xScale(d.percentage))
      .attr("y", d => yScale(d.ageBracket))
      .attr("width", d => xScale(d.percentage))
      .attr("height", yScale.bandwidth())
      .attr("fill", colorScale("male"))
      .style("cursor", "default");
    
    // female bars (right side)
    const femaleData = pas.filter(d => d.sex === "female");
    g.selectAll(".female-bar")
      .data(femaleData)
      .enter().append("rect")
      .attr("class", "female-bar")
      .attr("x", innerWidth / 2)
      .attr("y", d => yScale(d.ageBracket))
      .attr("width", d => xScale(d.percentage))
      .attr("height", yScale.bandwidth())
      .attr("fill", colorScale("female"))
      .style("cursor", "default");
    
    // percentage labels for males (left side)
    g.selectAll(".male-label")
      .data(maleData)
      .enter().append("text")
      .attr("class", "male-label")
      .attr("x", d => innerWidth / 2 - xScale(d.percentage) - 5)
      .attr("y", d => yScale(d.ageBracket) + yScale.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .attr("fill", "currentColor")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .text(d => d.percentage.toFixed(1) + "%");
    
    // percentage labels for females (right side)
    g.selectAll(".female-label")
      .data(femaleData)
      .enter().append("text")
      .attr("class", "female-label")
      .attr("x", d => innerWidth / 2 + xScale(d.percentage) + 5)
      .attr("y", d => yScale(d.ageBracket) + yScale.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .text(d => d.percentage.toFixed(1) + "%");
    
    // dynamic x-axis with grid lines and labels
    const maxValue = d3.max(pas, d => d.percentage);
    const xAxisTicks = xScale.ticks(4); 
    
    // vertical grid lines
    g.selectAll(".grid-line")
      .data(xAxisTicks.slice(1)) // skip 0
      .enter().append("g")
      .attr("class", "grid-line")
      .each(function(d) {
        const gridGroup = d3.select(this);
      });
    
    // x-axis labels
    g.selectAll(".x-axis-left")
      .data(xAxisTicks.slice(1)) // skip 0
      .enter().append("text")
      .attr("class", "x-axis-left")
      .attr("x", d => innerWidth / 2 - xScale(d))
      .attr("y", innerHeight + 20)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .text(d => d.toFixed(1) + "%");
    
    // right side x-axis (females)
    g.selectAll(".x-axis-right")
      .data(xAxisTicks.slice(1)) // skip 0
      .enter().append("text")
      .attr("class", "x-axis-right")
      .attr("x", d => innerWidth / 2 + xScale(d))
      .attr("y", innerHeight + 20)
      .attr("text-anchor", "middle")
      .attr("fill", "")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .text(d => d.toFixed(1) + "%");
    
    // bottom x-axis baseline
    g.append("line")
      .attr("x1", 0)
      .attr("x2", innerWidth)
      .attr("y1", innerHeight)
      .attr("y2", innerHeight)
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    
    // gender labels (below chart)
    g.append("text")
      .attr("x", innerWidth / 4)
      .attr("y", innerHeight + 40)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Male");
    
    g.append("text")
      .attr("x", innerWidth * 3 / 4)
      .attr("y", innerHeight + 40)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Female");
    
    // hover functionality
    ageBrackets.forEach(bracket => {
      const femaleRecord = pas.find(d => d.ageBracket === bracket && d.sex === "female");
      const maleRecord = pas.find(d => d.ageBracket === bracket && d.sex === "male");
      
      g.append("rect")
        .attr("class", "hover-area")
        .attr("x", 0)
        .attr("y", yScale(bracket))
        .attr("width", innerWidth)
        .attr("height", yScale.bandwidth())
        .attr("fill", "transparent")
        .style("cursor", "default")
        .on("mouseover", function(event) {
          // remove any existing tooltips
          d3.selectAll(".d3-tooltip").remove();
          
        // create Observable Plot default style tooltip with pointer
          const tooltip = d3.select("body").append("div")
            .attr("class", "d3-tooltip")
            .style("position", "absolute")
            .style("background", "white")
            .style("color", "black")
            .style("padding", "12px 16px")
            .style("border", "1px solid #000000")
            .style("font-family", "system-ui")
            .style("font-size", "12px")
            .style("font-weight", "normal")
            .style("line-height", "1.4")
            .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
            .style("pointer-events", "none")
            .style("z-index", "1000")
            .style("opacity", 0);
          
          const tooltipContent = `
            <div style="font-weight: bold; margin-bottom: 8px;">Age Bracket: ${bracket}</div>
            <div style="border-bottom: 1px solid #ddd; margin-bottom: 6px;"></div>
            <div style="">Female: ${femaleRecord?.percentage.toFixed(2) || '0.00'}% (${femaleRecord?.count.toFixed(0) || '0'} females)</div>
            <div style="margin-bottom: 4px;">Male: ${maleRecord?.percentage.toFixed(2) || '0.00'}% (${maleRecord?.count.toFixed(0) || '0'} males)</div>
          `;
          
          tooltip.html(tooltipContent)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")
            .transition()
            .duration(200)
            .style("opacity", 1);
        })
        .on("mousemove", function(event) {
          const tooltip = d3.select(".d3-tooltip");
          if (!tooltip.empty()) {
            tooltip
              .style("left", (event.pageX + 10) + "px")
              .style("top", (event.pageY - 10) + "px");
          }
        })
        .on("mouseout", function() {
          d3.selectAll(".d3-tooltip")
            .transition()
            .duration(200)
            .style("opacity", 0)
            .remove();
        });
    });
    
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`Population Distribution by Age and Sex, ${year}`);
    
    // subtitle
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(cityName);
  
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 10)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Age Bracket");

    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 20)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(xLabel + " (%)");
    
    return svg.node();
  }


// ------------------------------------------------------------
// plot_age
// ------------------------------------------------------------
function plot_age(pas, {
  width = plotWidth,
  height = plotWidth * heightRatio,
  cityName = globalCity,
  countryName = globalCountry
} = {}) {
  
  // get year for title
  const year = d3.max(pas, d => d.yearName);
  
  // aggregate data into three age groups, "working age (15-64 years)"; "young (under 15 years)"; and "elderly (65+ years)"
  const ageGroups = [
    {
      name: "Working Age",
      ageRange: "(15-64 years)",
      brackets: ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64"],
      color: "#009E73" // color-blind inclusive (https://davidmathlogic.com/colorblind/#%23000000-%23E69F00-%2356B4E9-%23009E73-%23F0E442-%230072B2-%23D55E00-%23CC79A7)
    },
    {
      name: "Youth", 
      ageRange: "(under 15 years)",
      brackets: ["0-4", "5-9", "10-14"],
      color: "#F0E442" // color-blind inclusive (https://davidmathlogic.com/colorblind/#%23000000-%23E69F00-%2356B4E9-%23009E73-%23F0E442-%230072B2-%23D55E00-%23CC79A7)
    },
    {
      name: "Elderly",
      ageRange: "(65+ years)", 
      brackets: ["65-69", "70-74", "75-79", "80+"],
      color: "#D55E00" // color-blind inclusive (https://davidmathlogic.com/colorblind/#%23000000-%23E69F00-%2356B4E9-%23009E73-%23F0E442-%230072B2-%23D55E00-%23CC79A7)
    }
  ];
  
  // calculate totals for each age group
  const processedData = ageGroups.map(group => {
    const groupData = pas.filter(d => group.brackets.includes(d.ageBracket));
    const totalCount = d3.sum(groupData, d => d.count);
    const totalPercentage = d3.sum(groupData, d => d.percentage);
    
    return {
      name: group.name,
      ageRange: group.ageRange,
      value: totalPercentage,
      count: totalCount,
      color: group.color
    };
  }).filter(d => d.value > 0); // only include age groups with data
  
  // create hierarchy data
  const hierarchyData = {
    name: `Population Distribution by Age Groups in ${cityName}`,
    children: processedData
  };
  
  // color scale based on the three age groups, "working age (15-64 years)"; "young (under 15 years)"; and "elderly (65+ years)"
  const colorScale = d3.scaleOrdinal()
    .domain(processedData.map(d => d.name))
    .range(processedData.map(d => d.color));
    
  // create hierarchy and layout
  const root = d3.hierarchy(hierarchyData)
    .sum(d => d.value)
    .sort((a, b) => b.value - a.value);
    
  d3.treemap()
    .size([width, height])
    .padding(2)
    .round(true)(root);
    
  // svg
  const svg = d3.create("svg")
    .attr("class", "plot")
    .attr("width", "100%")
    .attr("height", "auto")
    .attr("viewBox", `0 0 ${width} ${height + 60}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .style("max-width", "100%");

  // tooltip
  const tooltip = d3.select("body").append("div")
    .attr("class", "age-treemap-tooltip")
    .style("position", "absolute")
    .style("visibility", "hidden")
    .style("background", "white")
    .style("border", "1px solid black")
    .style("border-radius", "0px")
    .style("padding", "8px 12px")
    .style("font-family", "system-ui")
    .style("font-size", "12px")
    .style("color", "#333")
    .style("pointer-events", "none")
    .style("z-index", "1000")
    .style("line-height", "1.3");
    
  // create cells
  const leaf = svg.selectAll("g")
    .data(root.leaves())
    .join("g")
    .attr("transform", d => `translate(${d.x0},${d.y0 + 40})`);
    
  // age group rectangles with tooltips
  leaf.append("rect")
    .attr("fill", d => colorScale(d.data.name))
    .attr("fill-opacity", 0.8)
    .attr("stroke", "white")
    .attr("stroke-width", 2)
    .attr("width", d => d.x1 - d.x0)
    .attr("height", d => d.y1 - d.y0)
    .on("mouseover", function(event, d) {
      d3.select(this).attr("fill-opacity", 1);
      tooltip.style("visibility", "visible")
        .html(`
          <div style="font-weight: bold; margin-bottom: 6px;">${d.data.name}: ${d.data.ageRange}</div>
          <div style="border-bottom: 1px solid #ddd; margin: 6px 0;"></div>
          <div style="margin-bottom: 3px;">${d.data.value.toFixed(1)}% (${d.data.count.toFixed(0) || '0'} people) </div>
        `);
    })
    .on("mousemove", function(event) {
      const tooltipWidth = 220;
      const windowWidth = window.innerWidth;
      const mouseX = event.pageX;
      
      let leftPos = mouseX + 10;
      if (leftPos + tooltipWidth > windowWidth) {
        leftPos = mouseX - tooltipWidth - 10;
      }
      
      tooltip.style("top", (event.pageY - 35) + "px")
        .style("left", leftPos + "px");
    })
    .on("mouseout", function(event, d) {
      d3.select(this).attr("fill-opacity", 0.8);
      tooltip.style("visibility", "hidden");
    });
    
  // labels with dynamic text sizing and wrapping (matching plot_lc)
  leaf.filter(d => (d.x1 - d.x0) > 60 && (d.y1 - d.y0) > 35)
    .each(function(d) {
      const g = d3.select(this);
      const rectWidth = d.x1 - d.x0;
      
      // calculate dynamic font size based on rectangle size AND viewport
      const baseFontSize = Math.max(10, Math.min(18, rectWidth / 12));
      const viewportScale = Math.max(0.8, Math.min(1.4, width / 600));
      const dynamicFontSize = baseFontSize * viewportScale;
      
      // split long text into multiple lines for name
      const nameWords = d.data.name.split(/\s+/);
      const maxCharsPerLine = Math.floor(rectWidth / (dynamicFontSize * 0.6));
      let nameLines = [];
      let currentLine = "";
      
      nameWords.forEach(word => {
        if ((currentLine + word).length <= maxCharsPerLine) {
          currentLine += (currentLine ? " " : "") + word;
        } else {
          if (currentLine) nameLines.push(currentLine);
          currentLine = word;
        }
      });
      if (currentLine) nameLines.push(currentLine);
      
      // add name text lines with dynamic sizing
      nameLines.forEach((line, i) => {
        if (i < 2) {
          g.append("text")
            .attr("x", 4)
            .attr("y", 20 + (i * (dynamicFontSize + 2)))
            .style("font-family", "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
            .style("font-weight", "450")
            .style("font-size", `${dynamicFontSize}px`)
            .style("fill", "#333")
            .style("pointer-events", "none")
            .text(line);
        }
      });
      
      // split age range into multiple lines
      const rangeWords = d.data.ageRange.split(/\s+/);
      let rangeLines = [];
      currentLine = "";
      
      rangeWords.forEach(word => {
        if ((currentLine + word).length <= maxCharsPerLine) {
          currentLine += (currentLine ? " " : "") + word;
        } else {
          if (currentLine) rangeLines.push(currentLine);
          currentLine = word;
        }
      });
      if (currentLine) rangeLines.push(currentLine);
      
      // add age range text lines (slightly smaller and offset)
      const nameLineCount = Math.min(nameLines.length, 2);
      rangeLines.forEach((line, i) => {
        if (i < 1) { // only show first line of range
          g.append("text")
            .attr("x", 4)
            .attr("y", 20 + (nameLineCount * (dynamicFontSize + 2)) + (i * (dynamicFontSize * 0.8 + 2)))
            .style("font-family", "system-ui")
            .style("font-size", `${dynamicFontSize * 0.8}px`)
            .style("fill", "#333")
            .style("pointer-events", "none")
            .text(line);
        }
      });
    });
    
  // percentage labels with dynamic sizing
  leaf.filter(d => (d.x1 - d.x0) > 50 && (d.y1 - d.y0) > 50)
    .append("text")
    .attr("x", 4)
    .attr("y", d => {
      const rectWidth = d.x1 - d.x0;
      const baseFontSize = Math.max(8, Math.min(14, rectWidth / 10));
      const viewportScale = Math.max(0.8, Math.min(1.4, width / 600));
      return 50 + (baseFontSize * viewportScale);
    })
    .style("font-family", "system-ui")
    .style("font-size", d => {
      const rectWidth = d.x1 - d.x0;
      const baseFontSize = Math.max(7, Math.min(12, rectWidth / 12));
      const viewportScale = Math.max(0.8, Math.min(1.4, width / 600));
      return `${baseFontSize * viewportScale}px`;
    })
    .style("fill", "#141414")
    .style("pointer-events", "none")
    .text(d => `${d.data.value.toFixed(1)}%`);

  const container = d3.create("div").attr("class", "plot-container");

  // title
  svg.append("text")
    .attr("x", 0)
    .attr("y", 20)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Population Distribution by Age Groups, ${year}`);

  // subtitle
  svg.append("text")
    .attr("x", 0)
    .attr("y", 35)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(`${cityName}, ${countryName}`);

  container.node().appendChild(svg.node());
  return container.node();
}


// ------------------------------------------------------------
// plot_dependency
// ------------------------------------------------------------
function plot_dependency(pas, {
    width = plotWidth,
    cityName = globalCity,
    countryName = globalCountry
  } = {}) {
    
    // get year for title
    const year = d3.max(pas, d => d.yearName);
    
    // calculate dependency ratios
    const ratios = calculateAgeDependencyRatios(pas);
    
    // age group colors
    // color-blind inclusive (https://davidmathlogic.com/colorblind/#%23000000-%23E69F00-%2356B4E9-%23009E73-%23F0E442-%230072B2-%23D55E00-%23CC79A7)
    const colors = {
      youth: "#F0E442", // young (under 15 years) (yellow)
      elderly: "#D55E00", // elderly (65 + years)  (orange)
      workingAge: "#009E73", // working age (15-64 years), (purposely unused bubbles) (green)
      baseline: "currentColor" // baseline bubbles (gray)
    };
    
    // 100 bubbles data (10x10 grid)
    const bubbleData = [];
    let youthCount = 0;
    let elderlyCount = 0;
    
    for (let i = 0; i < 100; i++) {
      let type = "baseline";
      let color = colors.baseline;
      
      // assign young (under 15 years) (yellow) bubbles first
      if (youthCount < ratios.youthDependencyRatio) {
        type = "youth";
        color = colors.youth;
        youthCount++;
      }
      // assign elderly (65 + years) (orange) bubbles
      else if (elderlyCount < ratios.elderlyDependencyRatio) {
        type = "elderly"; 
        color = colors.elderly;
        elderlyCount++;
      }
      
      const row = Math.floor(i / 10);
      const col = i % 10;
      
      bubbleData.push({
        id: i,
        type: type,
        color: color,
        row: row,
        col: col
      });
    }
    
    // dimensions
    const bubbleSize = Math.min(width / 12, 40); // responsive bubble size
    const bubbleSpacing = bubbleSize * 1.2;
    const gridWidth = bubbleSpacing * 10;
    const gridHeight = bubbleSpacing * 10;
    const height = gridHeight + 160; // extra space for title + legend
    
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10px system-ui");
    
    // center the grid
    const offsetX = (width - gridWidth) / 2;
    const offsetY = 80; // space for title
    
    // tooltip
    const tooltip = d3.select("body").append("div")
      .attr("class", "dependency-bubble-tooltip")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "white")
      .style("border", "1px solid black")
      .style("border-radius", "0px")
      .style("padding", "8px 12px")
      .style("font-family", "system-ui")
      .style("font-size", "12px")
      .style("color", "#333")
      .style("pointer-events", "none")
      .style("z-index", "1000")
      .style("line-height", "1.3");
    
    // bubbles
    const bubbles = svg.selectAll(".bubble")
      .data(bubbleData)
      .enter().append("circle")
      .attr("class", "bubble")
      .attr("cx", d => offsetX + (d.col * bubbleSpacing) + bubbleSpacing/2)
      .attr("cy", d => offsetY + (d.row * bubbleSpacing) + bubbleSpacing/2)
      .attr("r", bubbleSize/2)
      .attr("fill", d => d.color)
      .attr("stroke", d => d.type === "baseline" ? "#dee2e6" : "white")
      .attr("stroke-width", 1)
      .attr("opacity", d => d.type === "baseline" ? 0.07 : 0.8)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.select(this).attr("opacity", d.type === "baseline" ? 0.6 : 1);
        
        let tooltipText = "";
        if (d.type === "youth") {
          // young (under 15 years) percentage of total population from age treemap data (pas)
          const youthPercentage = ((ratios.youthTotal / (ratios.youthTotal + ratios.workingAgeTotal + ratios.elderlyTotal)) * 100).toFixed(1);
          tooltipText = `
            <div style="font-weight: normal; margin-bottom: 6px;"><b>Youth Dependency Ratio</b>: ${ratios.youthDependencyRatio}:100</div>
            <div style="border-bottom: 1px solid #ddd; margin: 6px 0;"></div>
            <div><b>Young people</b> under the age of 15 years<br>
                  make up <b>${youthPercentage}%</b> of the total population<br>
                  and represent <b>${ratios.youthDependencyRatio}%</b> burden on the<br>
  working age population as dependents</div>
          `;
        } else if (d.type === "elderly") {
          // elderly (65+ years) percentage of total population from treemap data (pas)
          const elderlyPercentage = ((ratios.elderlyTotal / (ratios.youthTotal + ratios.workingAgeTotal + ratios.elderlyTotal)) * 100).toFixed(1);
          tooltipText = `
            <div style="font-weight: normal; margin-bottom: 6px;"><b>Elderly Dependency Ratio</b>: ${ratios.elderlyDependencyRatio}:100</div>
            <div style="border-bottom: 1px solid #ddd; margin: 6px 0;"></div>
            <div><b>Elderly people</b> over the age of 65 years<br>
                  make up <b>${elderlyPercentage}%</b> of the total population<br>
                  and represent <b>${ratios.elderlyDependencyRatio}%</b> burden on the<br>
                  working age population as dependents</div>
          `;
        } else {
          const workingAgePercentage = ((ratios.workingAgeTotal / (ratios.youthTotal + ratios.workingAgeTotal + ratios.elderlyTotal)) * 100).toFixed(1);
          tooltipText = `
            <div style="font-weight: normal; margin-bottom: 6px;"><b>Working Age Population</b>: ${workingAgePercentage}% of total</div>
            <div style="font-weight: normal; margin-bottom: 6px;"><b>Total Dependency Ratio</b>: ${ratios.totalDependencyRatio}:100</div>
            <div style="border-bottom: 1px solid #ddd; margin: 6px 0;"></div>
            <div><b>Working age people</b> between 15-64 years<br>
            make up <b>${workingAgePercentage}%</b> of the total population<br>
            and support <b>${ratios.youthDependencyRatio} youth</b> and <b>${ratios.elderlyDependencyRatio} elderly</b><br>
            dependents per 100 workers<br>
          `;
        }
        
        tooltip.style("visibility", "visible")
          .html(tooltipText);
      })
      .on("mousemove", function(event) {
        const tooltipWidth = 250;
        const windowWidth = window.innerWidth;
        const mouseX = event.pageX;
        
        let leftPos = mouseX + 10;
        if (leftPos + tooltipWidth > windowWidth) {
          leftPos = mouseX - tooltipWidth - 10;
        }
        
        tooltip.style("top", (event.pageY - 35) + "px")
          .style("left", leftPos + "px");
      })
      .on("mouseout", function(event, d) {
        d3.select(this).attr("opacity", d.type === "baseline" ? 0.07 : 0.8);
        tooltip.style("visibility", "hidden");
      });
    
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`Age Dependency Ratios, ${year}`);
  
    // subtitle  
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(`${cityName}, ${countryName}`);
    
    // legend with visual bubbles
    const legendY = offsetY + gridHeight + 40;
  
    // working age (15-64 years) legend item
    const workerLegend = svg.append("g")
      .attr("class", "worker-legend")
      .attr("transform", `translate(${width/2 - 100}, ${legendY -25})`);
    
    workerLegend.append("circle")
      .attr("cx", 8)
      .attr("cy", 8)
      .attr("r", 8)
      .attr("fill", "currentColor")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1)
      .attr("opacity", 0.07);
    
    workerLegend.append("text")
      .attr("x", 22)
      .attr("y", 8)
      .attr("dy", "0.35em")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`100 bubbles = 100 workers`);
  
    // young (under 15 years) legend item
    const youthLegend = svg.append("g")
      .attr("class", "youth-legend")
      .attr("transform", `translate(${width/2 - 100}, ${legendY})`);
    
    youthLegend.append("circle")
      .attr("cx", 8)
      .attr("cy", 8)
      .attr("r", 8)
      .attr("fill", colors.youth)
      .attr("stroke", "white")
      .attr("stroke-width", 1)
      .attr("opacity", 0.8);
    
    youthLegend.append("text")
      .attr("x", 22)
      .attr("y", 8)
      .attr("dy", "0.35em")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`= Youth dependent (${ratios.youthDependencyRatio} per 100 workers)`);
    
    // elderly (65 + years) legend item
    const elderlyLegend = svg.append("g")
      .attr("class", "elderly-legend")
      .attr("transform", `translate(${width/2 - 100}, ${legendY + 25})`);
    
    elderlyLegend.append("circle")
      .attr("cx", 8)
      .attr("cy", 8)
      .attr("r", 8)
      .attr("fill", colors.elderly)
      .attr("stroke", "white")
      .attr("stroke-width", 1)
      .attr("opacity", 0.8);
    
    elderlyLegend.append("text")
      .attr("x", 22)
      .attr("y", 8)
      .attr("dy", "0.35em")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`= Elderly dependent (${ratios.elderlyDependencyRatio} per 100 workers)`);
    
    // total dependency legend item  
    const totalLegend = svg.append("g")
      .attr("class", "total-legend")
      .attr("transform", `translate(${width/2 - 100}, ${legendY + 50})`);
    
    totalLegend.append("rect")
      .attr("x", 4)
      .attr("y", 4)
      .attr("width", 8)
      .attr("height", 8)
      .attr("fill", "none")
      .attr("stroke", "#666")
      .attr("stroke-width", 2);
    
    totalLegend.append("text")
      .attr("x", 22)
      .attr("y", 8)
      .attr("dy", "0.35em")
      .attr("fill", "currentColor")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`= Total dependency burden (${ratios.totalDependencyRatio} per 100 workers)`);
    
    return svg.node();
  }


// ------------------------------------------------------------
// plot_rwi_area
// ------------------------------------------------------------
function plot_rwi_area(rwi_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    color = "black"
  } = {}) {
    
    const sortedData = rwi_area.slice().sort((a, b) => 
      parseRwiCategory(a.bin) - parseRwiCategory(b.bin)
    );
  
    // color mapping for rwi wealth categories
    const rwiColorMap = {
      "Least wealthy": "#44b59c",
      "Less wealthy": "#94d1c0",
      "Average wealth": "#faf9c8",
      "More wealthy": "#faab90",
      "Most wealthy": "#eb765a"
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible rwi bins from data
    const allRwiBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allRwiBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.09),
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10px system-ui");
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => rwiColorMap[d.bin] || color)
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(rwiColorMap[d.bin] || color).darker(0.3))
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
  
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
          
        tooltip.html(`<div>RWI Wealth Category: ${d.bin}</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2)
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none");
  
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
   
   xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("dy", "1.5em");
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Relative Wealth Index Distribution");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Percentage of Area (%)");
      
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Relative Wealth Index");
      
    // caption
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Data: Meta Data for Good | Relative Wealth Index");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_uba_area
// ------------------------------------------------------------
function plot_uba_area(uba_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    color = "black"
  } = {}) {
    
    const sortedData = uba_area.slice().sort((a, b) => 
      parseUbaAreaRange(a.bin) - parseUbaAreaRange(b.bin)
    );
  
    // color mapping for years (same colors as City Scan, Built-Form, Urban Extent and Change, 1985-2015 map)
    const ubaAreaColorMap = {
      "Before 1986": "#f6f5d6",
      "1986-1995": "#e5c782",
      "1996-2005": "#cc7b6f",
      "2006-2015": "#62534e"
    };
  
    // map from bin values to year names (similar to binToConditionMap in plot_uba_area)
    const binToYearMap = {
      "Before 1986": "≤1985",
      "1986-1995": "1986-1995", 
      "1996-2005": "1996-2005",
      "2006-2015": "2006-2015"
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible uba bins
    const allUbaAreaBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allUbaAreaBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.12), // increased for condition labels
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => ubaAreaColorMap[d.bin] || color) // use d.year instead of d.bin // Reverted to d.bin because Before 1986 is a bin not a year; why did we do this in the first place?
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(ubaAreaColorMap[d.bin] || color).darker(0.3)) // use d.year instead of d.bin
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        // use condition name directly from data
        tooltip.html(`<div>Year: ${d.year}</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("dy", "1.5em") // label positioning slightly down
      .attr("font-weight", "normal");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Urban Built-Up Area Expansion");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Percentage of Area (%)");
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Year of Urban Expansion");
 
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Data: DLR, 2015, “World Settlement Footprint Evolution - Landsat 5/7 - Global");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_ubaa
// ------------------------------------------------------------
function plot_ubaa(uba, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Urban Built-up Area (sq km)",
  xLabel = "Year",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range for title
  const minYear = d3.min(uba, d => d.yearName);
  const maxYear = d3.max(uba, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([1, uba.length])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...uba.map(d => d.uba)) * 1.1])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d3.format("~s"));

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  const xTicks = Math.max(5, Math.min(15, Math.floor(width / 80)));
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(xTicks)
    .tickFormat(d => {
      const index = Math.round(d) - 1;
      return index >= 0 && index < uba.length ? d3.format("d")(uba[index].yearName) : "";
    })
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line (with defined function to skip null values)
  const line = d3.line()
    .defined(d => d.uba !== null)
    .x(d => xScale(d.year))
    .y(d => yScale(d.uba));
    
  g.append("path")
    .datum(uba)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // dots (filter out null values)
  g.selectAll(".dot")
    .data(uba.filter(d => d.uba !== null))
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.year))
    .attr("cy", d => yScale(d.uba))
    .attr("r", Math.max(2, Math.min(3, width / 200)))
    .attr("fill", "black")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>${yLabel}: ${d.uba.toLocaleString()}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Urban Built-up Area, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);
    
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_ubap
// ------------------------------------------------------------
function plot_ubap(uba, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Urban Built-up area Growth Percentage",
  xLabel = "Year",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range for title
  const minYear = d3.min(uba, d => d.yearName);
  const maxYear = d3.max(uba, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain(d3.extent(uba, d => d.yearName))
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...uba.map(d => d.ubaGrowthPercentage)) * 1.1])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d => d);

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d3.format("d"))
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line (with defined function to skip null values)
  const line = d3.line()
    .defined(d => d.ubaGrowthPercentage !== null)
    .x(d => xScale(d.yearName))
    .y(d => yScale(d.ubaGrowthPercentage));
    
  g.append("path")
    .datum(uba)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // dots (filter out null values)
  g.selectAll(".dot")
    .data(uba.filter(d => d.ubaGrowthPercentage !== null))
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.yearName))
    .attr("cy", d => yScale(d.ubaGrowthPercentage))
    .attr("r", Math.max(2, Math.min(3, width / 200)))
    .attr("fill", "black")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>Growth Percentage: ${d.ubaGrowthPercentage !== null ? d.ubaGrowthPercentage.toFixed(2) + '%' : 'N/A'}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Urban Built-up Area Growth Percentage, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel + " (%)");
    
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_lc
// ------------------------------------------------------------
function plot_lc(lc, {
    width = plotWidth,
    height = plotWidth * heightRatio, // maintains a 1.67:1 aspect ratio (width: height), note: 0.5 = wider chart (2:1 ratio); 0.75 = more square (1.33:1 ratio) 
    cityName = globalCity,
  } = {}) {
    
    // filter and prepare data
    const filtered = lc
      .filter(d => d.percentage > 0)
      .sort((a, b) => b.percentage - a.percentage);
      
    const hierarchyData = {
      name: `Land Cover in ${cityName}`,
      children: filtered.map(d => ({
        name: d.lcType,
        value: d.percentage,
        pixelCount: d.pixelCount
      }))
    };
    
  //color scale - dynamic mapping based on actual data
  const landCoverColors = {
    "Cropland": "#eaa86f",
    "Built up": "#d3605f", 
    "Grassland": "#9bbb7f",
    "Tree cover": "#629777",
    "Permanent water bodies": "#61acdc",
    "Shrubland": "#e2c985",
    "Bare sparse vegetation": "#b4ada4",
    "Herbaceous wetland": "#979ec9",
    "Snow and ice": "#e2e3e3",
    "Mangroves": "#48d394",
    "Moss and lichens": "#f6eba0"
  };
  
  // color scale based on actual data present
  const actualLandCoverTypes = hierarchyData.children.map(d => d.name);
  const colorScale = d3.scaleOrdinal()
    .domain(actualLandCoverTypes)
    .range(actualLandCoverTypes.map(type => landCoverColors[type] || "#cccccc"));
      
    // create hierarchy and layout
    const root = d3.hierarchy(hierarchyData)
      .sum(d => d.value)
      .sort((a, b) => b.value - a.value);
      
    d3.treemap()
      .size([width, height])
      .padding(2)
      .round(true)(root);
      
    // svg
    const svg = d3.create("svg")
      .attr("class", "plot")
      .attr("width", "100%") // "100%" instead of fixed, width
      .attr("height", "auto") //  "auto" instead of fixed, height + 40
      .attr("viewBox", `0 0 ${width} ${height + 60}`)
      .attr("preserveAspectRatio", "xMidYMid meet") 
      .style("max-width", "100%")  // prevent overflow
  
  
    // tooltip
    const tooltip = d3.select("body").append("div")
      .attr("class", "lc-treemap-tooltip")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "white")
      .style("border", "1px solid black")
      .style("border-radius", "0px")
      .style("padding", "8px 12px")
      .style("font-family", "system-ui")
      .style("font-size", "12px")
      .style("color", "#333")
      .style("pointer-events", "none")
      .style("z-index", "1000")
      .style("line-height", "1.3");
      
    // create cells
    const leaf = svg.selectAll("g")
      .data(root.leaves())
      .join("g")
      .attr("transform", d => `translate(${d.x0},${d.y0 + 40})`);
      
    // lc rectangles with tooltips
    leaf.append("rect")
      .attr("fill", d => colorScale(d.data.name))
      .attr("fill-opacity", 0.8)
      .attr("stroke", "white")
      .attr("stroke-width", 2)
      .attr("width", d => d.x1 - d.x0)
      .attr("height", d => d.y1 - d.y0)
      .on("mouseover", function(event, d) {
        d3.select(this).attr("fill-opacity", 1);
        tooltip.style("visibility", "visible")
          .html(`
            <div style="margin-bottom: 3px;"><strong>${d.data.name}</strong>: ${d.data.value.toFixed(1)}%</div>
          `);
      })
      .on("mousemove", function(event) {
        const tooltipWidth = 220;
        const windowWidth = window.innerWidth;
        const mouseX = event.pageX;
        
        let leftPos = mouseX + 10;
        if (leftPos + tooltipWidth > windowWidth) {
          leftPos = mouseX - tooltipWidth - 10;
        }
        
        tooltip.style("top", (event.pageY - 35) + "px")
          .style("left", leftPos + "px");
      })
      .on("mouseout", function(event, d) {
        d3.select(this).attr("fill-opacity", 0.8);
        tooltip.style("visibility", "hidden");
      });
      
    // labels with dynamic text sizing (improved scale, 03june2025)
    leaf.filter(d => (d.x1 - d.x0) > 60 && (d.y1 - d.y0) > 35)
      .each(function(d) {
        const g = d3.select(this);
        const rectWidth = d.x1 - d.x0;
        
        // calculate dynamic font size based on rectangle size AND viewport
        const baseFontSize = Math.max(10, Math.min(18, rectWidth / 12)); // increased min and max // Math.max(8, Math.min(16, rectWidth / 16)); //12
        const viewportScale = Math.max(0.8, Math.min(1.4, width / 600)); // new scaling range // Math.max(0.6, Math.min(1.2, width / 800)); // scale based on chart width
        const dynamicFontSize = baseFontSize * viewportScale;
        
        // split long text into multiple lines
        const words = d.data.name.split(/\s+/);
        const maxCharsPerLine = Math.floor(rectWidth / (dynamicFontSize * 0.6));
        let lines = [];
        let currentLine = "";
        
        words.forEach(word => {
          if ((currentLine + word).length <= maxCharsPerLine) {
            currentLine += (currentLine ? " " : "") + word;
          } else {
            if (currentLine) lines.push(currentLine);
            currentLine = word;
          }
        });
        if (currentLine) lines.push(currentLine);
        
        // text lines with dynamic sizing
        lines.forEach((line, i) => {
          if (i < 2) {
            g.append("text")
              .attr("x", 4)
              .attr("y", 20 + (i * (dynamicFontSize + 2)))
              .style("font-family", "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
              .style("font-weight", "450")
              .style("font-size", `${dynamicFontSize}px`)
              .style("fill", "#333")
              .style("pointer-events", "none")
              .text(line);
          }
        });
      });
      
    // percentage labels with dynamic sizing
    leaf.filter(d => (d.x1 - d.x0) > 50 && (d.y1 - d.y0) > 50)
      .append("text")
      .attr("x", 4)
      .attr("y", d => {
        const rectWidth = d.x1 - d.x0;
        const baseFontSize = Math.max(8, Math.min(14, rectWidth / 10)); // increased min and max // Math.max(6, Math.min(12, rectWidth / 12));
        const viewportScale = Math.max(0.8, Math.min(1.4, width / 600)); // new scaling range // Math.max(0.6, Math.min(1.2, width / 800));
        return 40 + (baseFontSize * viewportScale);
      })
      .style("font-family", "system-ui") //, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
      .style("font-size", d => {
        const rectWidth = d.x1 - d.x0;
        const baseFontSize = Math.max(7, Math.min(12, rectWidth / 12)); // increased min and max // Math.max(5, Math.min(10, rectWidth / 15));
        const viewportScale = Math.max(0.8, Math.min(1.4, width / 600)); // new scaling range // Math.max(0.6, Math.min(1.2, width / 800));
        return `${baseFontSize * viewportScale}px`;
      })
      .style("fill", "#141414")
      .style("pointer-events", "none")
      .text(d => `${d.data.value.toFixed(1)}%`);
  
    const container = d3.create("div").attr("class", "plot-container");
  
      // title
    svg.append("text")
      .attr("x", 0)
      .attr("y", 20)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(`Land Cover Types`);
  
    // subtitle
    svg.append("text")
      .attr("x", 0)
      .attr("y", 35)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(`${cityName}`);
    
    container.node().appendChild(svg.node());
    return container.node();
  }


// ------------------------------------------------------------
// plot_uddm
// ------------------------------------------------------------
function plot_uddm(pg, uba, pug, {
  cityName = globalCity,
  width = plotWidth,
  color = "black"
} = {}) {
  
  // calculate individual chart dimensions
  const chartWidth = (width - 80) / 2; 
  const chartHeight = chartWidth * 0.65; 
  const margin = {
    top: 60, // more room for title
    right: Math.max(20, chartWidth * 0.04),
    bottom: Math.max(55, chartWidth * 0.11), // more room for x-axis label
    left: Math.max(70, chartWidth * 0.14) // more room for y-axis label
  };
  const innerWidth = chartWidth - margin.left - margin.right;
  const innerHeight = chartHeight - margin.top - margin.bottom;
  
  // year ranges
  const pgYearRange = [d3.min(pg, d => d.yearName), d3.max(pg, d => d.yearName)];
  const ubaYearRange = [d3.min(uba, d => d.yearName), d3.max(uba, d => d.yearName)];
  const pugYearRange = [d3.min(pug, d => d.yearName), d3.max(pug, d => d.yearName)];
  
  // dynamic font sizes based on chart width
  const titleSize = Math.max(11, Math.min(14, chartWidth / 40));
  const axisLabelSize = Math.max(9, Math.min(11, chartWidth / 45));
  const tickLabelSize = Math.max(8, Math.min(10, chartWidth / 50));
  const strokeWidth = Math.max(1.2, Math.min(2, chartWidth / 350));
  const dotRadius = Math.max(1.2, Math.min(2.2, chartWidth / 220));
  
  // CHART 1: Population Growth (pga)
  function createChart1_pga() {
    const svg = d3.create("svg")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .style("background", "white");
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleLinear()
      .domain(d3.extent(pg, d => d.yearName))
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(...pg.map(d => d.population)) * 1.1])
      .range([innerHeight, 0]);
    
    // y-axis
    const yAxisGroup = g.append("g");
    yAxisGroup.call(d3.axisLeft(yScale)
      .ticks(Math.max(4, Math.min(6, Math.floor(innerHeight / 60))))
      .tickFormat(d => {
        if (d === 0) return "0";
        if (d >= 1000000) return `${(d/1000000).toFixed(d % 1000000 === 0 ? 0 : 1)}M`;
        if (d >= 1000) return `${(d/1000).toFixed(0)}K`;
        return d;
      })
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth));
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dx", "-0.3em");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxisGroup.call(d3.axisBottom(xScale)
      .ticks(Math.max(4, Math.min(7, Math.floor(innerWidth / 70))))
      .tickFormat(d3.format("d"))
      .tickSizeOuter(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dy", "0.7em");
    
    // line
    const line = d3.line()
      .defined(d => d.population !== null)
      .x(d => xScale(d.yearName))
      .y(d => yScale(d.population));
    
    g.append("path")
      .datum(pg)
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-width", strokeWidth)
      .attr("d", line);
    
    // dots with tooltips
    g.selectAll(".dot")
      .data(pg.filter(d => d.population !== null))
      .enter().append("circle")
      .attr("cx", d => xScale(d.yearName))
      .attr("cy", d => yScale(d.population))
      .attr("r", dotRadius)
      .attr("fill", "black")
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "6px 10px")
          .style("border", "1.5px solid #000")
          .style("font-family", "system-ui")
          .style("font-size", "11px")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
        tooltip.html(`<div>Year: ${d.yearName}</div><div>Population: ${d.population.toLocaleString()}</div>`)
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px")
          .transition().duration(200).style("opacity", 1);
      })
      .on("mousemove", function(event) {
        d3.select(".d3-tooltip")
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px");
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip").transition().duration(200).style("opacity", 0).remove();
      });
    
    // title
    svg.append("text")
      .attr("x", margin.left)
      .attr("y", 20)
      .attr("font-size", titleSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "500")
      .text(`Population Growth, ${pgYearRange[0]}-${pgYearRange[1]}`);
    
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Population");
    
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", chartHeight - 12)
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Year");
    
    return svg.node();
  }
  
  // CHART 2: Population Growth Percentage (pgp)
  function createChart2_pgp() {
    const svg = d3.create("svg")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .style("background", "white");
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleLinear()
      .domain(d3.extent(pg, d => d.yearName))
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(...pg.map(d => d.populationGrowthPercentage)) * 1.1])
      .range([innerHeight, 0]);
    
    // y-axis
    const yAxisGroup = g.append("g");
    yAxisGroup.call(d3.axisLeft(yScale)
      .ticks(Math.max(4, Math.min(6, Math.floor(innerHeight / 60))))
      .tickFormat(d => d)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth));
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dx", "-0.3em");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxisGroup.call(d3.axisBottom(xScale)
      .ticks(Math.max(4, Math.min(7, Math.floor(innerWidth / 70))))
      .tickFormat(d3.format("d"))
      .tickSizeOuter(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dy", "0.7em");
    
    // line
    const line = d3.line()
      .defined(d => d.populationGrowthPercentage !== null)
      .x(d => xScale(d.yearName))
      .y(d => yScale(d.populationGrowthPercentage));
    
    g.append("path")
      .datum(pg)
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-width", strokeWidth)
      .attr("d", line);
    
    // dots with tooltips
    g.selectAll(".dot")
      .data(pg.filter(d => d.populationGrowthPercentage !== null))
      .enter().append("circle")
      .attr("cx", d => xScale(d.yearName))
      .attr("cy", d => yScale(d.populationGrowthPercentage))
      .attr("r", dotRadius)
      .attr("fill", "black")
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "6px 10px")
          .style("border", "1.5px solid #000")
          .style("font-family", "system-ui")
          .style("font-size", "11px")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
        tooltip.html(`<div>Year: ${d.yearName}</div><div>Growth Percentage: ${d.populationGrowthPercentage.toFixed(2)}%</div>`)
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px")
          .transition().duration(200).style("opacity", 1);
      })
      .on("mousemove", function(event) {
        d3.select(".d3-tooltip")
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px");
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip").transition().duration(200).style("opacity", 0).remove();
      });
    
    // title
    svg.append("text")
      .attr("x", margin.left)
      .attr("y", 20)
      .attr("font-size", titleSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "500")
      .text(`Population Growth Percentage, ${pgYearRange[0]}-${pgYearRange[1]}`);
    
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Growth Percentage (%)");
    
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", chartHeight - 12)
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Year");
    
    return svg.node();
  }
  
  // CHART 3: Urban Built-up Area (ubaa)
  function createChart3_ubaa() {
    const svg = d3.create("svg")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .style("background", "white");
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleLinear()
      .domain([1, uba.length])
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(...uba.map(d => d.uba)) * 1.1])
      .range([innerHeight, 0]);
    
    // y-axis
    const yAxisGroup = g.append("g");
    yAxisGroup.call(d3.axisLeft(yScale)
      .ticks(Math.max(4, Math.min(6, Math.floor(innerHeight / 60))))
      .tickFormat(d3.format("~s"))
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth));
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dx", "-0.3em");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxisGroup.call(d3.axisBottom(xScale)
      .ticks(Math.max(4, Math.min(7, Math.floor(innerWidth / 70))))
      .tickFormat(d => {
        const index = Math.round(d) - 1;
        return index >= 0 && index < uba.length ? d3.format("d")(uba[index].yearName) : "";
      })
      .tickSizeOuter(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dy", "0.7em");
    
    // line
    const line = d3.line()
      .defined(d => d.uba !== null)
      .x(d => xScale(d.year))
      .y(d => yScale(d.uba));
    
    g.append("path")
      .datum(uba)
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-width", strokeWidth)
      .attr("d", line);
    
    // dots with tooltips
    g.selectAll(".dot")
      .data(uba.filter(d => d.uba !== null))
      .enter().append("circle")
      .attr("cx", d => xScale(d.year))
      .attr("cy", d => yScale(d.uba))
      .attr("r", dotRadius)
      .attr("fill", "black")
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "6px 10px")
          .style("border", "1.5px solid #000")
          .style("font-family", "system-ui")
          .style("font-size", "11px")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
        tooltip.html(`<div>Year: ${d.yearName}</div><div>Built-up Area: ${d.uba.toLocaleString()} sq km</div>`)
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px")
          .transition().duration(200).style("opacity", 1);
      })
      .on("mousemove", function(event) {
        d3.select(".d3-tooltip")
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px");
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip").transition().duration(200).style("opacity", 0).remove();
      });
    
    // title
    svg.append("text")
      .attr("x", margin.left)
      .attr("y", 20)
      .attr("font-size", titleSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "500")
      .text(`Urban Built-up Area, ${ubaYearRange[0]}-${ubaYearRange[1]}`);
    
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Built-up Area (sq km)");
    
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", chartHeight - 12)
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Year");
    
    return svg.node();
  }
  
  // CHART 4: Urban Built-up Area Growth Percentage (ubap)
  function createChart4_ubap() {
    const svg = d3.create("svg")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .style("background", "white");
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleLinear()
      .domain(d3.extent(uba, d => d.yearName))
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(...uba.map(d => d.ubaGrowthPercentage)) * 1.1])
      .range([innerHeight, 0]);
    
    // y-axis
    const yAxisGroup = g.append("g");
    yAxisGroup.call(d3.axisLeft(yScale)
      .ticks(Math.max(4, Math.min(6, Math.floor(innerHeight / 60))))
      .tickFormat(d => d)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth));
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dx", "-0.3em");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxisGroup.call(d3.axisBottom(xScale)
      .ticks(Math.max(4, Math.min(7, Math.floor(innerWidth / 70))))
      .tickFormat(d3.format("d"))
      .tickSizeOuter(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dy", "0.7em");
    
    // line
    const line = d3.line()
      .defined(d => d.ubaGrowthPercentage !== null)
      .x(d => xScale(d.yearName))
      .y(d => yScale(d.ubaGrowthPercentage));
    
    g.append("path")
      .datum(uba)
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-width", strokeWidth)
      .attr("d", line);
    
    // dots with tooltips
    g.selectAll(".dot")
      .data(uba.filter(d => d.ubaGrowthPercentage !== null))
      .enter().append("circle")
      .attr("cx", d => xScale(d.yearName))
      .attr("cy", d => yScale(d.ubaGrowthPercentage))
      .attr("r", dotRadius)
      .attr("fill", "black")
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "6px 10px")
          .style("border", "1.5px solid #000")
          .style("font-family", "system-ui")
          .style("font-size", "11px")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
        tooltip.html(`<div>Year: ${d.yearName}</div><div>Growth Percentage: ${d.ubaGrowthPercentage.toFixed(2)}%</div>`)
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px")
          .transition().duration(200).style("opacity", 1);
      })
      .on("mousemove", function(event) {
        d3.select(".d3-tooltip")
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px");
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip").transition().duration(200).style("opacity", 0).remove();
      });
    
    // title
    svg.append("text")
      .attr("x", margin.left)
      .attr("y", 20)
      .attr("font-size", titleSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "500")
      .text(`Built-up Area Growth %, ${ubaYearRange[0]}-${ubaYearRange[1]}`);
    
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Growth Percentage (%)");
    
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", chartHeight - 12)
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Year");
    
    return svg.node();
  }
  
  // CHART 5: Density (d)
  function createChart5_d() {
    const svg = d3.create("svg")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .style("background", "white");
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleLinear()
      .domain(d3.extent(pug, d => d.yearName))
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(...pug.map(d => d.density)) * 1.1])
      .range([innerHeight, 0]);
    
    // y-axis
    const yAxisGroup = g.append("g");
    yAxisGroup.call(d3.axisLeft(yScale)
      .ticks(Math.max(4, Math.min(6, Math.floor(innerHeight / 60))))
      .tickFormat(d3.format("~s"))
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth));
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dx", "-0.3em");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxisGroup.call(d3.axisBottom(xScale)
      .ticks(Math.max(4, Math.min(7, Math.floor(innerWidth / 70))))
      .tickFormat(d3.format("d"))
      .tickSizeOuter(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dy", "0.7em");
    
    // line
    const line = d3.line()
      .defined(d => d.density !== null)
      .x(d => xScale(d.yearName))
      .y(d => yScale(d.density));
    
    g.append("path")
      .datum(pug)
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-width", strokeWidth)
      .attr("d", line);
    
    // dots with tooltips
    g.selectAll(".dot")
      .data(pug.filter(d => d.density !== null))
      .enter().append("circle")
      .attr("cx", d => xScale(d.yearName))
      .attr("cy", d => yScale(d.density))
      .attr("r", dotRadius)
      .attr("fill", "black")
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "6px 10px")
          .style("border", "1.5px solid #000")
          .style("font-family", "system-ui")
          .style("font-size", "11px")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
        tooltip.html(`<div>Year: ${d.yearName}</div><div>Density: ${d.density.toFixed(0)} people/sq km</div>`)
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px")
          .transition().duration(200).style("opacity", 1);
      })
      .on("mousemove", function(event) {
        d3.select(".d3-tooltip")
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px");
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip").transition().duration(200).style("opacity", 0).remove();
      });
    
    // title
    svg.append("text")
      .attr("x", margin.left)
      .attr("y", 20)
      .attr("font-size", titleSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "500")
      .text(`Density, ${pugYearRange[0]}-${pugYearRange[1]}`);
    
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Density (people/sq km)");
    
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", chartHeight - 12)
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Year");
    
    return svg.node();
  }
  
  // CHART 6: Pop-Urban Growth Ratio (pug)
  function createChart6_pug() {
    const svg = d3.create("svg")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      .style("background", "white");
    
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    const xScale = d3.scaleLinear()
      .domain([0, 2])
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain(d3.extent(pug, d => d.yearName))
      .range([innerHeight, 0]);
    
    // y-axis
    const yAxisGroup = g.append("g");
    yAxisGroup.call(d3.axisLeft(yScale)
      .ticks(Math.max(4, Math.min(8, Math.floor(innerHeight / 50))))
      .tickFormat(d3.format("d"))
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth));
    yAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    yAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dx", "-0.3em");
    
    // x-axis
    const xAxisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxisGroup.call(d3.axisBottom(xScale)
      .ticks(2)
      .tickSizeOuter(0)
      .tickSizeInner(-innerHeight));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick line")
      .attr("stroke", "#e8e8e8")
      .attr("stroke-width", 0.8);
    xAxisGroup.selectAll(".tick text")
      .attr("font-size", tickLabelSize + "px")
      .attr("font-family", "system-ui")
      .attr("dy", "0.7em");
    
    // vertical dashed line at x=1
    g.append("line")
      .attr("x1", xScale(1))
      .attr("x2", xScale(1))
      .attr("y1", 0)
      .attr("y2", innerHeight)
      .attr("stroke", "#999")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "4,4");
    
    // line
    const line = d3.line()
      .defined(d => d.populationUrbanGrowthRatio !== null)
      .x(d => xScale(d.populationUrbanGrowthRatio))
      .y(d => yScale(d.yearName));
    
    g.append("path")
      .datum(pug)
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-width", strokeWidth)
      .attr("d", line);
    
    // dots with tooltips
    g.selectAll(".dot")
      .data(pug.filter(d => d.populationUrbanGrowthRatio !== null))
      .enter().append("circle")
      .attr("cx", d => xScale(d.populationUrbanGrowthRatio))
      .attr("cy", d => yScale(d.yearName))
      .attr("r", dotRadius)
      .attr("fill", "black")
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "6px 10px")
          .style("border", "1.5px solid #000")
          .style("font-family", "system-ui")
          .style("font-size", "11px")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
        tooltip.html(`<div>Year: ${d.yearName}</div><div>Pop-Urban Growth Ratio: ${d.populationUrbanGrowthRatio.toFixed(2)}</div>`)
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px")
          .transition().duration(200).style("opacity", 1);
      })
      .on("mousemove", function(event) {
        d3.select(".d3-tooltip")
          .style("left", (event.pageX - 50) + "px")
          .style("top", (event.pageY - 50) + "px");
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip").transition().duration(200).style("opacity", 0).remove();
      });
    
    // annotations
    const minYear = d3.min(pug, d => d.yearName);
    const annotationSize = Math.max(9, Math.min(11, chartWidth / 45));
    const annotationY = margin.top + yScale(minYear) - 10;
    
    svg.append("text")
      .attr("x", margin.left + xScale(1))
      .attr("y", annotationY + 40)
      .attr("text-anchor", "middle")
      .attr("font-size", annotationSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "600")
      .attr("fill", "#555")
      .text("Balanced");
    
    svg.append("text")
      .attr("x", margin.left + xScale(0.5))
      .attr("y", annotationY + 40)
      .attr("text-anchor", "middle")
      .attr("font-size", (annotationSize - 1) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "600")
      .attr("fill", "#555")
      .text("Potential");
    
    svg.append("text")
      .attr("x", margin.left + xScale(0.5))
      .attr("y", annotationY + 50)
      .attr("text-anchor", "middle")
      .attr("font-size", (annotationSize - 1) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "600")
      .attr("fill", "#555")
      .text("Sprawl");
    
    svg.append("text")
      .attr("x", margin.left + xScale(1.5))
      .attr("y", annotationY + 40)
      .attr("text-anchor", "middle")
      .attr("font-size", (annotationSize - 1) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "600")
      .attr("fill", "#555")
      .text("Potential");
    
    svg.append("text")
      .attr("x", margin.left + xScale(1.5))
      .attr("y", annotationY + 50)
      .attr("text-anchor", "middle")
      .attr("font-size", (annotationSize - 1) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "600")
      .attr("fill", "#555")
      .text("Densification");
    
    // title
    svg.append("text")
      .attr("x", margin.left)
      .attr("y", 20)
      .attr("font-size", titleSize + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "500")
      .text(`Pop-Urban Growth Ratio, ${pugYearRange[0]}-${pugYearRange[1]}`);
    
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 15)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("font-size", axisLabelSize + "px")
      .attr("font-family", "system-ui")
      .text("Year");
    
    return svg.node();
  }
  
  // create all charts
  const chart1 = createChart1_pga();
  const chart2 = createChart2_pgp();
  const chart3 = createChart3_ubaa();
  const chart4 = createChart4_ubap();
  const chart5 = createChart5_d();
  const chart6 = createChart6_pug();
  
  // create container div with grid layout
  const container = html`<div style="
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto auto;
    gap: 30px;
    max-width: ${width}px;
    margin: 0 auto;
    padding: 20px 0;
  ">
    <div style="grid-column: 1 / -1; text-align: left; margin-bottom: 0px;">
      <h2 style="margin: 0; font-size: ${Math.max(16, Math.min(20, width / 50))}px; font-weight: 500; color: #222;">Urban Development Dynamics</h2>
      <h3 style="margin: 5px 0 0 0; font-size: ${Math.max(14, Math.min(18, width / 55))}px; font-style: italic; font-weight: 400; color: #555;">${cityName}</h3>
    </div>
    <div>${chart1}</div>
    <div>${chart2}</div>
    <div>${chart3}</div>
    <div>${chart4}</div>
    <div>${chart5}</div>
    <div>${chart6}</div>
  </div>`;
  
  return container;
}


// ------------------------------------------------------------
// plot_pv_area
// ------------------------------------------------------------
function plot_pv_area(pv_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    color = "black"
  } = {}) {
    
    const sortedData = pv_area.slice().sort((a, b) => 
      parsePvAreaRange(a.bin) - parsePvAreaRange(b.bin)
    );
  
    // color mapping for condition levels (same colors as plot_pv_alt)
    const pvAreaColorMap = {
      "Less than Favorable": "#FF9800",
      "Favorable": "#FFC107",
      "Excellent": "#4CAF50"
    };
  
    // map from bin values to condition names (similar to dangerMapping in plot_fwi_d)
    const binToConditionMap = {
      "<3.5": "Less than Favorable",
      "3.5-4.5": "Favorable", 
      ">4.5": "Excellent"
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible pv bins
    const allPvAreaBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allPvAreaBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(110, width * 0.12), // increased for condition labels
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => pvAreaColorMap[d.condition] || color) // use d.condition instead of d.bin
      .attr("fill-opacity", 0.4)
      .attr("stroke", d => d3.color(pvAreaColorMap[d.condition] || color).darker(0.3)) // use d.condition instead of d.bin
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        // use condition name directly from data
        tooltip.html(`<div>Condition: ${d.condition}</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("dy", "1.5em");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Photovoltaic Power Potential Yield");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Percentage of Area (%)");
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Power Potential of a Theoretical 1 kWp PV System (kWh)");
  
    // condition labels above x-axis bins
    completeData.forEach(d => {
      const conditionName = binToConditionMap[d.bin];
      if (conditionName) {
        svg.append("text")
          .attr("x", margin.left + xScale(d.bin) + xScale.bandwidth()/2)
          .attr("y", margin.top + innerHeight + 35) // position above x-axis labels
          .attr("text-anchor", "middle")
          .attr("fill", "currentColor")
          .attr("font-size", Math.max(9, Math.min(11, width / 80)) + "px")
          .attr("font-family", "system-ui")
          .attr("font-weight", "normal")
          .text(conditionName);
      }
    });
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Data: Solargis/World Bank, Global Solar Atlas 2 | Condition Classification: World Bank");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_pv_alt
// ------------------------------------------------------------
function plot_pv_alt(pv, {
  cityName = globalCity,
  width = plotWidth,
  xLabel = "Month",
  yLabel = "Daily PV Energy Yield (kWh/kWp)",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(80, width * 0.1),
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // condition level threshold categories
  const conditionCategories = [
    { name: "Excellent", min: 4.5, max: Infinity, color: "#4CAF50", opacity: 0.40 },
    { name: "Favorable", min: 3.5, max: 4.5, color: "#FFC107", opacity: 0.40 },
    { name: "Less than Favorable", min: 0, max: 3.5, color: "#FF9800", opacity: 0.40 },
  ];
  
  // determine which condition levels are relevant based on data range
  const maxPv = Math.max(...pv.map(d => d.maxPv));
  const yDomain = [0, maxPv * 1.1];
  
  // filter condition levels that intersect with the visible range
  const visibleCategories = conditionCategories.filter(cat => 
    cat.min < yDomain[1] && cat.max > yDomain[0]
  );
  
  // scales
  const xScale = d3.scaleBand()
    .domain(d3.range(1, 13))
    .range([0, innerWidth])
    .padding(0.1);
  
  const yScale = d3.scaleLinear()
    .domain(yDomain)
    .range([innerHeight, 0]);
  
  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");
  
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // condition bands (background)
  visibleCategories.forEach(cat => {
    g.append("rect")
      .attr("x", 0)
      .attr("y", yScale(Math.min(cat.max, yDomain[1])))
      .attr("width", innerWidth)
      .attr("height", yScale(Math.max(cat.min, yDomain[0])) - yScale(Math.min(cat.max, yDomain[1])))
      .attr("fill", cat.color)
      .attr("fill-opacity", cat.opacity)
      .attr("stroke", cat.color)
      .attr("stroke-opacity", 0.3)
      .attr("stroke-width", 0.5);
  });
  
  // condition labels (only for bands with sufficient height)
  visibleCategories
    .filter(cat => {
      const bandHeight = Math.min(cat.max, yDomain[1]) - Math.max(cat.min, yDomain[0]);
      const pixelHeight = (bandHeight / yDomain[1]) * innerHeight;
      return pixelHeight > 25;
    })
    .forEach(cat => {
      const yPos = (yScale(Math.max(cat.min, yDomain[0])) + yScale(Math.min(cat.max, yDomain[1]))) / 2;
      g.append("text")
        .attr("x", innerWidth - 5)
        .attr("y", yPos)
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", cat.color === "#FFC107" ? "#B8860B" : cat.color)
        .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
        .attr("font-weight", "bold")
        .attr("font-family", "system-ui")
        .text(cat.name);
    });
  
  // y-axis
  const yAxisGroup = g.append("g");
  yAxisGroup.call(d3.axisLeft(yScale)
    .ticks(Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60)))
    .tickSizeOuter(0));
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick text")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("dx", "-0.3em");
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("transform", `translate(0,${innerHeight})`);
  xAxisGroup.call(d3.axisBottom(xScale)
    .tickFormat(d => pv[d-1]?.monthName || "")
    .tickSizeOuter(0));
  xAxisGroup.select(".domain").attr("stroke", "currentColor");
 
  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line
  const line = d3.line()
    .x(d => xScale(d.month) + xScale.bandwidth() / 2)
    .y(d => yScale(d.maxPv));
  
  g.append("path")
    .datum(pv)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // dots with tooltips
  g.selectAll(".dot")
    .data(pv)
    .enter().append("circle")
    .attr("cx", d => xScale(d.month) + xScale.bandwidth() / 2)
    .attr("cy", d => yScale(d.maxPv))
    .attr("r", Math.max(2, Math.min(3, width / 200)))
    .attr("fill", "black")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();
      
      // determine condition category
      const pvValue = d.maxPv;
      const conditionCategory = conditionCategories.find(cat => 
        pvValue >= cat.min && pvValue < cat.max
      ) || conditionCategories[conditionCategories.length - 1];
      
      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
      
      tooltip.html(`<div>Month: ${d.monthName}</div><div>Daily PV energy yield: ${pvValue.toFixed(2)} kWh/kWp</div><div>Conditions: ${conditionCategory.name}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 70) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 70) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Seasonal Availability of Solar Energy, January - December");
  
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
  
  // caption
  svg.append("text")
    .attr("x", 20)
    .attr("y", height - 10)
    .attr("text-anchor", "start")
    .attr("fill", "#666")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .text("Data: Solargis/World Bank, Global Solar Atlas 2 | Condition Classification: World Bank");
  
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);
  
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 55)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
  
  return svg.node();
}


// ------------------------------------------------------------
// plot_pv_d
// ------------------------------------------------------------
function plot_pv_d(pv, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Condition",
  xLabel = "Month",
  showPercentages = true
} = {}) {
  
  const height = width * heightRatio;
  const scaleFactor = width / 800;
  const minScale = 0.6;
  const maxScale = 1.5;
  const dynamicScale = Math.max(minScale, Math.min(maxScale, scaleFactor));
  
  const margin = {
    top: 70,
    right: Math.max(180, width * 0.25, 180 * dynamicScale), // increased right margin for labels
    bottom: Math.max(90, width * 0.1, 50 * dynamicScale),
    left: Math.max(150, width * 0.15, 120 * dynamicScale) // increased left margin for wrapped text
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // count occurrences of each condition level
  const conditionCounts = d3.rollup(pv, v => v.length, d => d.condition);
  
  // define all possible condition levels in order
  const allConditionLevels = [
    "Excellent", "Favorable", "Less than Favorable"
  ];
  
  // condition mapping
  const conditionMapping = {
    "Excellent": "Excellent",
    "Favorable": "Favorable",
    "Less than Favorable": "Less than Favorable",
  };
  
  // data array with counts and percentages
  const distributionData = allConditionLevels.map(level => ({
    condition: level,
    count: conditionCounts.get(conditionMapping[level]) || 0,
    percentage: ((conditionCounts.get(conditionMapping[level]) || 0) / pv.length * 100)
  }));
  
  // color mapping for condition levels
  const colorMap = {
    "Excellent": "#4CAF50",
    "Favorable": "#FFC107",
    "Less than Favorable": "#8B0000",
  };
  
  // calculate domain max
  const maxCount = Math.max(...distributionData.map(d => d.count));
  const tickStep = Math.ceil(maxCount / 10) || 1;
  const lastTick = Math.ceil(maxCount / tickStep) * tickStep;
  const domainMax = lastTick;
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([0, domainMax])
    .range([0, innerWidth]);
  
  const yScale = d3.scaleBand()
    .domain(allConditionLevels)
    .range([0, innerHeight])
    .padding(0.2);
  
  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", Math.max(12, Math.min(18, 14 * dynamicScale)) + "px system-ui");
  
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // grid lines
  const xAxisGrid = d3.axisBottom(xScale)
    .ticks(Math.max(4, Math.min(10, Math.floor(innerWidth / 80))))
    .tickSize(innerHeight)
    .tickFormat("");
  
  g.append("g")
    .attr("class", "grid")
    .call(xAxisGrid)
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-opacity", 1)
      .attr("stroke-width", 1));
  
  // background "dummy" bars
  g.selectAll(".dummy-bar")
    .data(distributionData)
    .enter().append("rect")
    .attr("class", "dummy-bar")
    .attr("x", 0)
    .attr("y", d => yScale(d.condition))
    .attr("width", xScale(domainMax))
    .attr("height", yScale.bandwidth())
    .attr("fill", "#f8f9fa")
    .attr("fill-opacity", 0.3)
    .attr("stroke", "#dee2e6")
    .attr("stroke-width", Math.max(0.5, 1 * dynamicScale));
  
  // actual data bars
  g.selectAll(".data-bar")
    .data(distributionData.filter(d => d.count > 0))
    .enter().append("rect")
    .attr("class", "data-bar")
    .attr("x", 0)
    .attr("y", d => yScale(d.condition))
    .attr("width", d => xScale(d.count))
    .attr("height", yScale.bandwidth())
    .attr("fill", d => colorMap[d.condition])
    .attr("fill-opacity", 0.40)
    .attr("stroke", "white")
    .attr("stroke-opacity", 0.3)
    .attr("stroke-width", Math.max(0.5, 1 * dynamicScale));
  
  // text labels (positioned outside the bars for readability)
  g.selectAll(".label")
    .data(distributionData)
    .enter().append("text")
    .attr("class", "label")
    .attr("x", xScale(domainMax) + 10) // position outside grey "dummy" bar
    .attr("y", d => yScale(d.condition) + yScale.bandwidth() / 2)
    .attr("text-anchor", "start")
    .attr("dominant-baseline", "middle")
    .attr("fill", d => d.count > 0 ? "black" : "#6c757d")
    .attr("font-size", Math.max(9, Math.min(13, 11 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("font-style", d => d.count > 0 ? "normal" : "italic")
    .text(d => d.count > 0 ?
      (showPercentages ? `${d.count} months (${d.percentage.toFixed(1)}%)` : `${d.count} months`) :
      "0 months (0.0%)");
  
  // y-axis with wrapped text labels
  const yAxisGroup = g.append("g");
  yAxisGroup.call(d3.axisLeft(yScale)
    .tickSize(0)
    .tickPadding(10));
  yAxisGroup.select(".domain").remove();
  
  // replace text with wrapped text
  yAxisGroup.selectAll(".tick text").remove();
  yAxisGroup.selectAll(".tick")
    .append("foreignObject")
    .attr("width", margin.left - 15)
    .attr("height", yScale.bandwidth())
    .attr("x", -(margin.left - 15))
    .attr("y", -yScale.bandwidth() / 2)
    .append("xhtml:div")
    .style("width", (margin.left - 15) + "px")
    .style("height", yScale.bandwidth() + "px")
    .style("display", "flex")
    .style("align-items", "center")
    .style("justify-content", "flex-end")
    .style("font-size", Math.max(10, Math.min(14, 12 * dynamicScale)) + "px")
    .style("font-family", "system-ui")
    .style("text-align", "right")
    .style("line-height", "1.2")
    .html(d => d);
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("transform", `translate(0,${innerHeight})`);
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(4, Math.min(10, Math.floor(innerWidth / 80))))
    .tickSize(Math.max(3, 6 * dynamicScale))
    .tickSizeOuter(0));
  xAxisGroup.select(".domain").attr("stroke", "currentColor");
  xAxisGroup.selectAll(".tick text")
    .attr("font-size", Math.max(10, Math.min(14, 12 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("dy", "0.5em");
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Photovoltaic Potential Condition Level Distribution");
  
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(`${cityName} (${pv.length}-month period)`);
  
  // caption
  svg.append("text")
    .attr("x", 20)
    .attr("y", height - 10)
    .attr("text-anchor", "start")
    .attr("fill", "#666")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .text("Data: Solargis/World Bank, Global Solar Atlas 2 | Condition Classification: World Bank");
  
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", Math.max(11, Math.min(16, 13 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);
  
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 55)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", Math.max(11, Math.min(16, 13 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
  
  return svg.node();
}


// ------------------------------------------------------------
// plot_pv
// ------------------------------------------------------------
function plot_pv(pv, {
  cityName = globalCity, 
  countryName = globalCountry,
  width = plotWidth,
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // scales
  const xScale = d3.scaleBand()
    .domain(pv.map(d => d.monthName))
    .range([0, innerWidth])
    .padding(0.1);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...pv.map(d => d.maxPv)) * 1.1])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d3.format("~s"));

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal");
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal");
  
  // horizontal dashed lines for conditions
  g.append("line")
    .attr("x1", 0)
    .attr("x2", innerWidth)
    .attr("y1", yScale(4.5))
    .attr("y2", yScale(4.5))
    .attr("stroke", "gray")
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "5,5");
    
  g.append("line")
    .attr("x1", 0)
    .attr("x2", innerWidth)
    .attr("y1", yScale(3.5))
    .attr("y2", yScale(3.5))
    .attr("stroke", "gray")
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "5,5");
  
  // condition labels
  g.append("text")
    .attr("x", innerWidth / 2)
    .attr("y", yScale(4.5) - 8)
    .attr("text-anchor", "middle")
    .attr("fill", "gray")
    .attr("font-size", "14px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "bold")
    .text("Excellent Conditions");
    
  g.append("text")
    .attr("x", innerWidth / 2)
    .attr("y", yScale(3.5) - 8)
    .attr("text-anchor", "middle")
    .attr("fill", "gray")
    .attr("font-size", "14px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "bold")
    .text("Favorable Conditions");
  
  // line
  const line = d3.line()
    .x(d => xScale(d.monthName) + xScale.bandwidth() / 2)
    .y(d => yScale(d.maxPv));
    
  g.append("path")
    .datum(pv)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // dots
  g.selectAll(".dot")
    .data(pv)
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.monthName) + xScale.bandwidth() / 2)
    .attr("cy", d => yScale(d.maxPv))
    .attr("r", Math.max(2, Math.min(3, width / 200)))
    .attr("fill", "black")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Month: ${d.monthName}</div><div>Daily PV energy yield: ${d.maxPv} kWh/kWp</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Seasonal Availability of Solar Energy, January - December");
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(`${cityName}, ${countryName}`);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Daily PV energy yield (kWh/kWp)");
    
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Month");
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_aq
// ------------------------------------------------------------
function plot_aq(aq_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    color = "black"
  } = {}) {
    
    const sortedData = aq_area.slice().sort((a, b) => 
      parseAirQualityRange(a.bin) - parseAirQualityRange(b.bin)
    );
  
    // air quality colors given current mapped colors
    const airQualityColorMap = {
      "0-5": "#fff7de",           // [0-5)
      "5-10": "#f8dbc4",          // [5-10)
      "10-15": "#eec0ae",         // [10-15)
      "15-20": "#e0a79d",         // [15-20)
      "20-30": "#d5949f",         // [20-30)
      "30-40": "#cf94aa" ,        // [30-40)
      "40-50": "#c394b5",         // [40-50)
      "50-100": "#c394b5" ,       // [50-100)
      "100+": "#a07ca0" ,         // [100+)
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible air quality concentrations of PM2.5 µg/mˆ3 bins
    const allAirQualityBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allAirQualityBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.1),
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // SVG
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => airQualityColorMap[d.bin] || color) // use mapped color or fallback, "color"
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(airQualityColorMap[d.bin] || color).darker(0.5)) //use mapped color or fallback, "color"
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        tooltip.html(`<div>PM 2.5: ${d.bin} µg/m<sup>3</sup></div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
 
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("dy", "1.5em") // label positioning slightly down
      .attr("font-weight", "normal");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Air Quality");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Percentage of Area (%)");
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Concentrations of PM2.5");
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_summer_area
// ------------------------------------------------------------
function plot_summer_area(summer_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    color = "#ff6b35"
  } = {}) {
    
    const sortedData = summer_area.slice().sort((a, b) => {
      const aTemp = parseInt(a.bin.split('-')[0]);
      const bTemp = parseInt(b.bin.split('-')[0]);
      return aTemp - bTemp;
    });
  
    // get temperature range from data
    const minTemp = parseInt(sortedData[0].bin.split('-')[0]);
    const maxTemp = parseInt(sortedData[sortedData.length - 1].bin.split('-')[1]);
    
    // color scale (for visual cohesion with summer surface temperature map), where: blue, cool (cooler temperatures) to red, hot (hotter temperatures) gradient
    const colorScale = d3.scaleLinear()
      .domain([
        minTemp, 
        minTemp + (maxTemp - minTemp) * 0.33,
        minTemp + (maxTemp - minTemp) * 0.67,
        maxTemp
      ])
      .range(["#8db4d4", "#d3daba", "#f2cb94", "#e37b74"])
      .interpolate(d3.interpolateRgb);
  
    // alternative hexcodes - cold to hot gradient that is technically not visually cohesive with the summer surface temperature map (i.e, did not select via hexcode finder), however they "look" more cohesive - 
  
      // "20-25": "#d4e8f7", (blue)
      // "25-30": "#a8d5ed",
      // "30-35": "#7ec3e3",
      // "35-40": "#f9c74f",
      // "40-45": "#f8961e",
      // "45-50": "#f3722c",
      // "50-55": "#f94144" (red)
    
    // create color map for all temperature bins in data
    const tempColorMap = {};
    sortedData.forEach(d => {
      // Use the midpoint of each bin for color mapping
      const binStart = parseInt(d.bin.split('-')[0]);
      const binEnd = parseInt(d.bin.split('-')[1]);
      const binMidpoint = (binStart + binEnd) / 2;
      tempColorMap[d.bin] = colorScale(binMidpoint);
    });
      
    // calculate total to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible temperature bins from data
    const allTempBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allTempBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.09), // reduced -  since no type labels
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10px system-ui");
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y axis with grid lines
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with temperature color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => tempColorMap[d.bin] || color)
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(tempColorMap[d.bin] || color).darker(0.3))
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        d3.selectAll(".d3-tooltip").remove();
  
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        tooltip.html(`<div>Temperature: ${d.bin}°C</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for bars
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2)
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none");
  
    // x axis
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Summer Surface Temperature Distribution");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Percentage of Area (%)");
      
    // x-axis label
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Mean Surface Temperature (°C)");
      
    // caption
    svg.append("text")
      .attr("x", 20)
      .attr("y", height)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Data: Landsat Level 2 Surface Temperature Science Product courtesy of the U.S. Geological Survey.");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_ndvi_area
// ------------------------------------------------------------
function plot_ndvi_area(ndvi_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    color = "black"
  } = {}) {
    
    const sortedData = ndvi_area.slice().sort((a, b) => 
      parseNdviRange(a.bin) - parseNdviRange(b.bin)
    );
  
    // color mapping for coverage "type" (same colors as mapped)
    const ndviColorMap = {
      "Water": "#b2b2d5",
      "Built-up": "#eff4d8",
      "Barren": "#cfe4c7",
      "Shrub and Grassland": "#a5cd9f",
      "Sparse": "#82b685",
      "Dense": "#82b685"
    };
  
    // map from bin values to "type" (similar to binToConditionMap in plot_pv_alt)
    const binToTypeMap = {
      "-1-0.015": "Water",
      "0.015-0.14": "Built-up", 
      "0.14-0.18": "Barren", 
      "0.18-0.27": "Shrub and Grassland",
      "0.27-0.36": "Sparse",
      "0.36-1": "Dense"
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible ndvi bins
    const allNdviBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allNdviBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.12), // increased for type labels
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => ndviColorMap[d.type] || color) // use d.type instead of d.bin
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(ndviColorMap[d.type] || color).darker(0.3)) // use d.type instead of d.bin
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        // use condition name directly from data
        tooltip.html(`<div>Coverage: ${d.type}</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);

    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("dy", "1.5em");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Vegetated Areas");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Percentage of Area (%)");
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 35)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Normalized Difference Vegetation Index (NDVI)");
  
    // condition labels above x-axis bins
    completeData.forEach(d => {
      const typeName = binToTypeMap[d.bin];
      if (typeName) {
        svg.append("text")
          .attr("x", margin.left + xScale(d.bin) + xScale.bandwidth()/2)
          .attr("y", margin.top + innerHeight + 35) // position above x-axis labels
          .attr("text-anchor", "middle")
          .attr("fill", "currentColor")
          .attr("font-size", Math.max(9, Math.min(11, width / 80)) + "px")
          .attr("font-family", "system-ui")
          .attr("font-weight", "normal")
          .text(typeName);
      }
    });
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Data: European Space Agency, 2020 | Normalized Difference Vegetation Index");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_fe
// ------------------------------------------------------------
function plot_fe(fe, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Year",
  xLabel = "Month",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get unique months for x-axis
  const monthNames = {
       1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
       7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
     };
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([0.5, 12.5])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([1980, 2026])
    .range([innerHeight, 0]);
  
  // size scale for bubbles based on displaced count
  const maxDisplaced = d3.max(fe, d => d.DISPLACED);
  const minDisplaced = d3.min(fe, d => d.DISPLACED);
  const rScale = d3.scaleSqrt()
    .domain([minDisplaced, maxDisplaced])
    .range([Math.max(3, Math.min(8, width / 150)), Math.max(15, Math.min(40, width / 25))]);
  
  // color scale
  const colorScale = d3.scaleOrdinal()
    .domain(["Large event", "Very large event"])
    .range(["#87CEEB", "#000080"]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTickInterval = Math.max(5, Math.min(10, Math.floor((width * 0.6) / 40)));
  const yTickValues = d3.range(1985, 2026, yTickInterval);
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .tickValues(yTickValues)
    .tickFormat(d3.format("d"))
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth);

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  // x-axis with grid lines
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .tickValues(d3.range(1, 13))
    .tickFormat(d => monthNames[d] || "")
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // dots (bubbles) with tooltips
  g.selectAll(".dot")
    .data(fe)
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.begin_month))
    .attr("cy", d => yScale(d.begin_year))
    .attr("r", d => rScale(d.DISPLACED))
    .attr("fill", d => colorScale(d.severity))
    .attr("fill-opacity", 0.7)
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(0.5, Math.min(2, width / 400)))
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>${d.line1}:</div><div><br/>${d.line2},<br/>${d.line3}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 80) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 80) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Large flood events, 1985-2025");
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
  
  // legend
  const legendX = width - 180;
  const legendY = 25;
  const legendSpacing = 25;
  
  const legendGroup = svg.append("g")
    .attr("class", "legend");
  
  ["Large event", "Very large event"].forEach((severity, i) => {
    const legendItem = legendGroup.append("g")
      .attr("transform", `translate(${legendX}, ${legendY + i * legendSpacing})`);
    
    legendItem.append("circle")
      .attr("cx", 8)
      .attr("cy", 0)
      .attr("r", 6)
      .attr("fill", colorScale(severity))
      .attr("fill-opacity", 0.7)
      .attr("stroke", "black")
      .attr("stroke-width", 1);
    
    legendItem.append("text")
      .attr("x", 20)
      .attr("y", 0)
      .attr("dy", "0.32em")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .text(severity);
  });
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);

  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_fu
// ------------------------------------------------------------
function plot_fu(fu, {
  cityName = globalCity,
  width = plotWidth,
  xLabel = "Year",
  yLabel = "Exposed Urban Built-up Area (sq km)",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range
  const minYear = d3.min(fu, d => d.yearName);
  const maxYear = d3.max(fu, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([1, fu.length])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...fu.map(d => d.fu)) * 1.2])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d3.format("~s"));

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  // x-axis with grid lines
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d => {
      const index = Math.round(d) - 1;
      return index >= 0 && index < fu.length ? d3.format("d")(fu[index].yearName) : "";
    })
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line (with defined function to skip null values)
  const line = d3.line()
    .defined(d => d.fu !== null)
    .x(d => xScale(d.year))
    .y(d => yScale(d.fu));
    
  g.append("path")
    .datum(fu)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // invisible dots for tooltips (line chart style - no visible dots)
  g.selectAll(".dot")
    .data(fu.filter(d => d.fu !== null))
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.year))
    .attr("cy", d => yScale(d.fu))
    .attr("r", 4) // slightly larger invisible hit area
    .attr("fill", "transparent")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>${yLabel}: ${d.fu.toLocaleString()}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Built-up Area Exposed to Fluvial Flooding, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);

  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_pu
// ------------------------------------------------------------
function plot_pu(pu, {
  cityName = globalCity,
  width = plotWidth,
  xLabel = "Year",
  yLabel = "Exposed Urban Built-up Area (sq km)",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range
  const minYear = d3.min(pu, d => d.yearName);
  const maxYear = d3.max(pu, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([1, pu.length])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...pu.map(d => d.pu)) * 1.2])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d3.format("~s"));

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  // x-axis with grid lines
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d => {
      const index = Math.round(d) - 1;
      return index >= 0 && index < pu.length ? d3.format("d")(pu[index].yearName) : "";
    })
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line (with defined function to skip null values)
  const line = d3.line()
    .defined(d => d.pu !== null)
    .x(d => xScale(d.year))
    .y(d => yScale(d.pu));
    
  g.append("path")
    .datum(pu)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // invisible dots for tooltips
  g.selectAll(".dot")
    .data(pu.filter(d => d.pu !== null))
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.year))
    .attr("cy", d => yScale(d.pu))
    .attr("r", 4)
    .attr("fill", "transparent")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>${yLabel}: ${d.pu.toLocaleString()}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Built-up Area Exposed to Pluvial Flooding, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);

  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
    
  return svg.node();
}


// ------------------------------------------------------------
// plot_cu
// ------------------------------------------------------------
function plot_cu(cu, {
  cityName = globalCity,
  width = plotWidth,
  xLabel = "Year",
  yLabel = "Exposed Urban Built-up Area (sq km)",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range
  const minYear = d3.min(cu, d => d.yearName);
  const maxYear = d3.max(cu, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([1, cu.length])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...cu.map(d => d.cu)) * 1.2])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d3.format("~s"));

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  // x-axis with grid lines
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d => {
      const index = Math.round(d) - 1;
      return index >= 0 && index < cu.length ? d3.format("d")(cu[index].yearName) : "";
    })
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line (with defined function to skip null values)
  const line = d3.line()
    .defined(d => d.cu !== null)
    .x(d => xScale(d.year))
    .y(d => yScale(d.cu));
    
  g.append("path")
    .datum(cu)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // invisible dots for tooltips
  g.selectAll(".dot")
    .data(cu.filter(d => d.cu !== null))
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(d.year))
    .attr("cy", d => yScale(d.cu))
    .attr("r", 4)
    .attr("fill", "transparent")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Year: ${d.yearName}</div><div>${yLabel}: ${d.cu.toLocaleString()}</div>`)
        .style("left", (event.pageX - 60) + "px")
        .style("top", (event.pageY - 60) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Built-up Area Exposed to Coastal Flooding, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);

  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
  return svg.node();
}


// ------------------------------------------------------------
// plot_comb
// ------------------------------------------------------------
function plot_comb(comb, pu, fu, cu, {
  cityName = globalCity,
  width = plotWidth,
  xLabel = "Year",
  yLabel = "Exposed Urban Built-up Area (sq km)",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.02), 
    bottom: Math.max(90, width * 0.1),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // get year range
  const minYear = d3.min(comb, d => d.yearName);
  const maxYear = d3.max(comb, d => d.yearName);
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([1, comb.length])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain([0, Math.max(...comb.map(d => d.comb)) * 1.2])
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // y-axis with grid lines
  const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  const yAxisCall = d3.axisLeft(yScale)
    .ticks(yTicks)
    .tickSizeOuter(0)
    .tickSizeInner(-innerWidth)
    .tickFormat(d3.format("~s"));

  yAxisGroup.call(yAxisCall);
  yAxisGroup.select(".domain").remove();
  yAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);
  yAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dx", "-0.3em");
  
  // x-axis with grid lines
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(5, Math.min(15, Math.floor(width / 80))))
    .tickFormat(d => {
      const index = Math.round(d) - 1;
      return index >= 0 && index < comb.length ? d3.format("d")(comb[index].yearName) : "";
    })
    .tickSizeOuter(0)
    .tickSizeInner(-innerHeight));
  xAxisGroup.select(".domain")
    .attr("stroke", "currentColor")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick line")
    .attr("stroke", "#f0f0f0")
    .attr("stroke-width", 1);

  xAxisGroup.selectAll(".tick text")
    .attr("fill", "currentColor")
    .attr("font-size", "10px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .attr("dy", "1.5em");
  
  // line generator
  const lineGenerator = d3.line()
    .x(d => xScale(d.year))
    .y((d, dataset) => {
      if (dataset === 'comb') return yScale(d.comb);
      if (dataset === 'pu') return yScale(d.pu);
      if (dataset === 'fu') return yScale(d.fu);
      if (dataset === 'cu') return yScale(d.cu);
    });
  
  const dashArray = `${Math.max(2, Math.min(6, width / 200))},${Math.max(2, Math.min(6, width / 200))}`;
  const strokeWidth = Math.max(1.5, Math.min(3, width / 400));
  
  // coastal line (cu) - green dashed
  g.append("path")
    .datum(cu)
    .attr("fill", "none")
    .attr("stroke", "#02b939")
    .attr("stroke-width", strokeWidth)
    .attr("stroke-dasharray", dashArray)
    .attr("d", d3.line()
      .defined(d => d.cu !== null)
      .x(d => xScale(d.year))
      .y(d => yScale(d.cu)));
  
  // fluvial line (fu) - red dashed
  g.append("path")
    .datum(fu)
    .attr("fill", "none")
    .attr("stroke", "#f8766d")
    .attr("stroke-width", strokeWidth)
    .attr("stroke-dasharray", dashArray)
    .attr("d", d3.line()
      .defined(d => d.fu !== null)
      .x(d => xScale(d.year))
      .y(d => yScale(d.fu)));
  
  // pluvial line (pu) - blue dashed
  g.append("path")
    .datum(pu)
    .attr("fill", "none")
    .attr("stroke", "#619cfe")
    .attr("stroke-width", strokeWidth)
    .attr("stroke-dasharray", dashArray)
    .attr("d", d3.line()
      .defined(d => d.pu !== null)
      .x(d => xScale(d.year))
      .y(d => yScale(d.pu)));
  
  // combined line (comb) - black solid
  g.append("path")
    .datum(comb)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", strokeWidth)
    .attr("d", d3.line()
      .defined(d => d.comb !== null)
      .x(d => xScale(d.year))
      .y(d => yScale(d.comb)));
  
  // invisible interaction area for tooltips
  g.selectAll(".interaction-area")
    .data(comb.filter(d => d.comb !== null))
    .enter().append("rect")
    .attr("class", "interaction-area")
    .attr("x", d => xScale(d.year) - 5)
    .attr("y", 0)
    .attr("width", 10)
    .attr("height", innerHeight)
    .attr("fill", "transparent")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();
      
      // find corresponding values for this year in all datasets
      const puValue = pu.find(p => p.year === d.year)?.pu || 0;
      const fuValue = fu.find(f => f.year === d.year)?.fu || 0;
      const cuValue = cu.find(c => c.year === d.year)?.cu || 0;

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div><strong>Year: ${d.yearName}</strong></div><div>━━━━━━━━━━━━</div><div>Combined: ${d.comb} sq km</div><div>&nbsp;</div><div>Pluvial: ${puValue.toFixed(1)} sq km</div><div>Fluvial: ${fuValue.toFixed(1)} sq km</div><div>Coastal: ${cuValue.toFixed(1)} sq km</div>`)
        .style("left", (event.pageX - 80) + "px")
        .style("top", (event.pageY - 100) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 80) + "px")
          .style("top", (event.pageY - 100) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px") 
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(`Built-up Area Exposed to Combined Flooding, ${minYear}-${maxYear}`);
    
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
  
  // legend
  const legendData = [
    { label: "Combined", color: "black", dashed: false },
    { label: "River", color: "#f8766d", dashed: true },
    { label: "Rainwater", color: "#619cfe", dashed: true },
    { label: "Coastal", color: "#02b939", dashed: true }
  ];
  
  const legendX = width - 160;
  const legendY = 25;
  const legendSpacing = 22;
  
  const legendGroup = svg.append("g")
    .attr("class", "legend");
  
  legendData.forEach((item, i) => {
    const legendItem = legendGroup.append("g")
      .attr("transform", `translate(${legendX}, ${legendY + i * legendSpacing})`);
    
    legendItem.append("line")
      .attr("x1", 0)
      .attr("x2", 20)
      .attr("y1", 0)
      .attr("y2", 0)
      .attr("stroke", item.color)
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", item.dashed ? "4,4" : "0");
    
    legendItem.append("text")
      .attr("x", 25)
      .attr("y", 0)
      .attr("dy", "0.32em")
      .attr("font-size", "12px")
      .attr("font-family", "system-ui")
      .text(item.label);
  });
    
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);

  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
  return svg.node();
}


// ------------------------------------------------------------
// plot_e
// ------------------------------------------------------------
function plot_e(e, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    xLabel = "Elevation (MASL)",
    yLabel = "Percentage of Area (%)",
    color = "black"
  } = {}) {
    
    const sortedData = e.slice().sort((a, b) => 
      parseElevationRange(a.bin) - parseElevationRange(b.bin)
    );
  
    // elevation colors given current mapped colors where 0 = lowest MASL bin and 4 = highest MASL bin
    const elevationColors = {
      0: "#f9d7d4",  // elevation_0 (lowest)
      1: "#e3b9c5",  // elevation_1
      2: "#cd9db8",  // elevation_2
      3: "#b682ac",  // elevation_3
      4: "#9f65a0"   // elevation_4 (highest)
    };
  
    // color mapping based on elevation order
    const elevationColorMap = {};
    sortedData.forEach((d, index) => {
      elevationColorMap[d.bin] = elevationColors[index];
    });
    
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible elevation bins
    const allElevationBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allElevationBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.1),
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
    
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
      
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => elevationColorMap[d.bin] || color) // use mapped color or fallback, "color"
      .attr("fill-opacity",1)
      .attr("stroke", d => d3.color(elevationColorMap[d.bin] || color).darker(0.5)) //use mapped color or fallback, "color"
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip - Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // pointer arrow for tooltip, add using css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // border for arrow for tooltip
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        tooltip.html(`<div>Elevation: ${d.bin} MASL</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position of tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot defaulty styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("dy", "1.5em");
    
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Elevation");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(yLabel);
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(xLabel);
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_s
// ------------------------------------------------------------
function plot_s(s, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    xLabel = "Slope (°)",
    yLabel = "Percentage of Area (%)",
    color = "black"
  } = {}) {
    
    const sortedData = s.slice().sort((a, b) => 
      parseSlopeRange(a.bin) - parseSlopeRange(b.bin)
    );
  
    // slope colors given current mapped colors
    const slopeColorMap = {
      "0-2": "#f9f9db",           // slope_lessthan2degrees
      "2-5": "#ebd5b4",           // slope_2to5degrees
      "5-10": "#dab38f",          // slope_5to10degrees
      "10-20": "#c88f6e",         // slope_10to20degrees
      "20-90": "#b26b4a"          // slope_greaterthan20degrees
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible slope bins
    const allSlopeBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allSlopeBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(90, width * 0.1),
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => slopeColorMap[d.bin] || color) // use mapped color or fallback, "color"
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(slopeColorMap[d.bin] || color).darker(0.5)) //use mapped color or fallback, "color"
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        tooltip.html(`<div>Slope: ${d.bin}°</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("dy", "1.5em");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Slope");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(yLabel);
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(xLabel);
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_ls_area
// ------------------------------------------------------------
function plot_ls_area(ls_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    xLabel = "Landslide Susceptibility",
    yLabel = "Percentage of Area (%)",
    color = "black"
  } = {}) {
    
    const sortedData = ls_area.slice().sort((a, b) => 
      parseLsAreaRange(a.bin) - parseLsAreaRange(b.bin)
    );
  
    // color mapping for landslide susceptibility (same colors as landslide map)
    const lsAreaColorMap = {
      "1": "#f6efe5",
      "2": "#f1cda8",
      "3": "#e9ac81",
      "4": "#dc8b6d",
      "5": "#b27365",
    };
  
    // map from bins to susceptbility values (similar to binToCondition in plot_pv_area)
    const binToSusceptibilityMap = {
      "Very low": "1",
      "Low": "2", 
      "Medium": "3", 
      "High": "4", 
      "Very high": "5"
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible bins
    const allLsAreaBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allLsAreaBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(110, width * 0.12), // increased for bin labels
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => lsAreaColorMap[d.susceptibility] || color) // use d.susceptibility instead of d.bin
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(lsAreaColorMap[d.susceptibility] || color).darker(0.3)) // use d.susceptibility instead of d.bin
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        // use condition name directly from data
        tooltip.html(`<div>Landslide Susceptibility: ${d.susceptibility}</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("dy", "1.5em")
      .attr("font-weight", "normal");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Landslide Susceptibility");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(yLabel);
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(xLabel);
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Data: NASA, 'Landslide Susceptibility Map'");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_l_area
// ------------------------------------------------------------
function plot_l_area(l_area, {
    cityName = globalCity, 
    countryName = globalCountry,
    width = plotWidth,
    xLabel = "Liquefaction Susceptibility",
    yLabel = "Percentage of Area (%)",
    color = "black"
  } = {}) {
    
    const sortedData = l_area.slice().sort((a, b) => 
      parseLAreaRange(a.bin) - parseLAreaRange(b.bin)
    );
  
    // color mapping for liquefaction susceptibility (same colors as liquefaction map)
    const lAreaColorMap = {
      "1": "#f6efe5",
      "2": "#f1cda8",
      "3": "#e9ac81",
      "4": "#dc8b6d",
      "5": "#b27365",
    };
  
    // map from bins to susceptbility values (similar to binToSusceptibilityMap in plot_ls_area)
    const binToSusceptibilityMap = {
      "Very low": "1",
      "Low": "2", 
      "Medium": "3", 
      "High": "4", 
      "Very high": "5"
    };
      
    // calculate total area to show complete distribution
    const totalCount = sortedData.reduce((sum, d) => sum + d.count, 0);
    
    // define all possible bins
    const allLAreaBins = sortedData.map(d => d.bin);
    
    // complete data with gray bars for visual completeness
    const completeData = allLAreaBins.map(bin => {
      const existing = sortedData.find(d => d.bin === bin);
      return existing || { bin, count: 0, percentage: 0 };
    });
    
    const height = width * heightRatio;
    const margin = {
      top: 70,
      right: Math.max(20, width * 0.02), 
      bottom: Math.max(110, width * 0.12), // increased for bin labels
      left: Math.max(80, width * 0.08)
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const xScale = d3.scaleBand()
      .domain(completeData.map(d => d.bin))
      .range([0, innerWidth])
      .padding(0.1);
      
    const yScale = d3.scaleLinear()
      .domain([0, 100])
      .range([innerHeight, 0]);
  
    // svg
    const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "white")
      .style("font", "10 px system-ui"); // Observable Plot default styling to match other plots
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // y-axis with grid lines (behind bars)
    const yTicks = Math.max(4, Math.min(10, Math.floor(width * 0.6) / 60));
    const yAxisGroup = g.append("g").attr("class", "y-axis");
    const yAxisCall = d3.axisLeft(yScale)
      .ticks(yTicks)
      .tickSizeOuter(0)
      .tickSizeInner(-innerWidth)
      .tickFormat(d3.format("~s"));
  
    // y-axis to match Observable Plot default styling
    yAxisGroup.call(yAxisCall);
    yAxisGroup.select(".domain").remove();
    yAxisGroup.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-width", 1);
    yAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal");
      
    // gray background bars for all bins
    g.selectAll(".background-bar")
      .data(completeData)
      .enter().append("rect")
      .attr("class", "background-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", 0)
      .attr("height", innerHeight)
      .attr("fill", "#f8f9fa")
      .attr("stroke", "#dee2e6")
      .attr("stroke-width", 0.5)
      .attr("fill-opacity", 0.3);
      
    // actual data bars with color mapping
    g.selectAll(".data-bar")
      .data(completeData.filter(d => d.percentage > 0))
      .enter().append("rect")
      .attr("class", "data-bar")
      .attr("x", d => xScale(d.bin))
      .attr("width", xScale.bandwidth())
      .attr("y", d => yScale(d.percentage))
      .attr("height", d => innerHeight - yScale(d.percentage))
      .attr("fill", d => lAreaColorMap[d.susceptibility] || color) // use d.susceptibility instead of d.bin
      .attr("fill-opacity", 1)
      .attr("stroke", d => d3.color(lAreaColorMap[d.susceptibility] || color).darker(0.3)) // use d.susceptibility instead of d.bin
      .attr("stroke-width", 1)
      .style("cursor", "default")
      .on("mouseover", function(event, d) {
        // remove any existing tooltips
        d3.selectAll(".d3-tooltip").remove();
  
        // tooltip = create Observable Plot default style tooltip with pointer
        const tooltip = d3.select("body").append("div")
          .attr("class", "d3-tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("color", "black")
          .style("padding", "8px 12px")
          .style("border", "1.8px solid #000000")
          .style("font-family", "system-ui")
          .style("font-size", "12px")
          .style("font-weight", "normal")
          .style("line-height", "1.4")
          .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
          .style("pointer-events", "none")
          .style("z-index", "1000")
          .style("opacity", 0);
                  
        // tooltip, add pointer arrow with css
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid white");
  
        // tooltip - border for arrow
        tooltip.append("div")
          .style("position", "absolute")
          .style("bottom", "-7px")
          .style("left", "50%")
          .style("transform", "translateX(-50%)")
          .style("width", "0")
          .style("height", "0")
          .style("border-left", "7px solid transparent")
          .style("border-right", "7px solid transparent")
          .style("border-top", "7px solid #ccc");
          
        // use condition name directly from data
        tooltip.html(`<div>Liquefaction Susceptibility: ${d.susceptibility}</div><div>Percentage of Area: ${d.percentage.toFixed(1)}%</div>`)
          .style("left", (event.pageX - 60) + "px")
          .style("top", (event.pageY - 60) + "px")
          .transition()
          .duration(200)
          .style("opacity", 1);
      })
      .on("mousemove", function(event, d) {
        // only update position if tooltip exists
        const tooltip = d3.select(".d3-tooltip");
        if (!tooltip.empty()) {
          tooltip
            .style("left", (event.pageX - 60) + "px")
            .style("top", (event.pageY - 60) + "px");
        }
      })
      .on("mouseout", function() {
        d3.selectAll(".d3-tooltip")
          .transition()
          .duration(200)
          .style("opacity", 0)
          .remove();
      });
  
    // text labels for all bars (to match Observable Plot default styling - lighter weight)
    g.selectAll(".bar-label")
      .data(completeData)
      .enter().append("text")
      .attr("x", d => xScale(d.bin) + xScale.bandwidth()/2)
      .attr("y", d => d.percentage > 0 ? 
        yScale(d.percentage) - 8 : 
        innerHeight/2) // center for zero values
      .attr("text-anchor", "middle")
      .attr("fill", d => d.percentage > 0 ? "black" : "#6c757d")
      .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("font-style", d => d.percentage > 0 ? "normal" : "italic")
      .text(d => d.percentage > 0 ? 
        `${d.percentage.toFixed(1)}%` : 
        "0.0%")
      .style("display", d => d.percentage > 2 || d.percentage === 0 ? "block" : "none"); // show labels for significant values or zeros
  
    // x-axis - to match Observable Plot default styling
    const xAxisGroup = g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`);
      
    xAxisGroup.call(d3.axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSizeInner(0));
    xAxisGroup.select(".domain")
      .attr("stroke", "currentColor")
      .attr("stroke-width", 1);
    xAxisGroup.selectAll(".tick text")
      .attr("fill", "currentColor")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .attr("dy", "1.5em");
      
    if (width < 500) {
      xAxisGroup.selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");
    }
      
    // title
    svg.append("text")
      .attr("x", 20)
      .attr("y", 25)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "18px") 
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("Liquefaction Susceptibility");
      
    // subtitle
    const titleLocation = countryName ? `${cityName}, ${countryName}` : cityName;
    svg.append("text")
      .attr("x", 20)
      .attr("y", 45)
      .attr("text-anchor", "start")
      .attr("fill", "currentColor")
      .attr("font-size", "16px")
      .attr("font-family", "system-ui")
      .attr("font-style", "italic")
      .attr("font-weight", "normal")
      .text(titleLocation);
      
    // y-axis label - to match Observable Plot default styling
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 20)
      .attr("x", -(margin.top + innerHeight/2))
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(yLabel);
      
    // x-axis label - to match Observable Plot defaulty styling
    svg.append("text")
      .attr("x", margin.left + innerWidth/2)
      .attr("y", height - 45)
      .attr("text-anchor", "middle")
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text(xLabel);
      
    // caption (add in text later if necessary)
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 15)
      .attr("text-anchor", "start")
      .attr("fill", "#6c757d")
      .attr("font-size", "9px")
      .attr("font-family", "system-ui")
      .attr("font-weight", "normal")
      .text("");
      
    return svg.node();
  }


// ------------------------------------------------------------
// plot_fwi
// ------------------------------------------------------------
function plot_fwi(fwi, {
  cityName = globalCity,
  width = plotWidth,
  xLabel = "Month",
  yLabel = "95th Percentile FWI",
  color = "black"
} = {}) {
  
  const height = width * heightRatio;
  const margin = {
    top: 70,
    right: Math.max(20, width * 0.05),
    bottom: Math.max(90, width * 0.12),
    left: Math.max(80, width * 0.08)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // EFFIS FWI risk category thresholds
  const riskCategories = [
    { name: "Very Low Risk", min: 0, max: 5.2, color: "#4CAF50", opacity: 0.40 },
    { name: "Low Risk", min: 5.2, max: 11.2, color: "#8BC34A", opacity: 0.40 },
    { name: "Moderate Risk", min: 11.2, max: 21.3, color: "#FFC107", opacity: 0.40 },
    { name: "High Risk", min: 21.3, max: 38.0, color: "#FF9800", opacity: 0.40 },
    { name: "Very High Risk", min: 38.0, max: 50, color: "#F44336", opacity: 0.40 },
    { name: "Extreme Risk", min: 50, max: Infinity, color: "#8B0000", opacity: 0.40 }
  ];
  
  // determine which risk categories are relevant based on data range
  const maxFWI = Math.max(...fwi.map(d => d.fwi));
  const yDomain = [0, maxFWI * 1.1];
  
  // filter categories that intersect with the visible range
  const visibleCategories = riskCategories.filter(cat => 
    cat.min < yDomain[1] && cat.max > yDomain[0]
  );
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([1, fwi.length])
    .range([0, innerWidth]);
    
  const yScale = d3.scaleLinear()
    .domain(yDomain)
    .range([innerHeight, 0]);

  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", "10px system-ui");

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // risk bands (background)
  visibleCategories.forEach(cat => {
    g.append("rect")
      .attr("x", xScale(1))
      .attr("y", yScale(Math.min(cat.max, yDomain[1])))
      .attr("width", xScale(fwi.length) - xScale(1))
      .attr("height", yScale(Math.max(cat.min, yDomain[0])) - yScale(Math.min(cat.max, yDomain[1])))
      .attr("fill", cat.color)
      .attr("fill-opacity", cat.opacity)
      .attr("stroke", cat.color)
      .attr("stroke-opacity", 0.3)
      .attr("stroke-width", 0.5);
  });
  
  // risk labels (only for bands with sufficient height)
  visibleCategories
    .filter(cat => {
      const bandHeight = Math.min(cat.max, yDomain[1]) - Math.max(cat.min, yDomain[0]);
      const pixelHeight = (bandHeight / yDomain[1]) * innerHeight;
      return pixelHeight > 25;
    })
    .forEach(cat => {
      const yPos = (yScale(Math.max(cat.min, yDomain[0])) + yScale(Math.min(cat.max, yDomain[1]))) / 2;
      g.append("text")
        .attr("x", innerWidth - 5)
        .attr("y", yPos)
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", cat.color === "#FFC107" ? "#B8860B" : cat.color)
        .attr("font-size", Math.max(9, Math.min(12, width / 60)) + "px")
        .attr("font-weight", "bold")
        .attr("font-family", "system-ui")
        .text(cat.name);
    });
  
  // y-axis
  const yAxisGroup = g.append("g").attr("class", "y-axis");
  yAxisGroup.call(d3.axisLeft(yScale)
    .ticks(Math.max(4, Math.min(10, Math.floor((width * 0.6) / 60))))
    .tickSizeOuter(0));
  yAxisGroup.select(".domain").attr("stroke", "currentColor");
  yAxisGroup.selectAll(".tick text")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("dx", "-0.3em");
  
  // x-axis (only show first week of each month)
  const monthTicks = d3.range(1, 53).filter(week => {
    const currentMonth = fwi[week-1]?.monthName;
    const prevMonth = week > 1 ? fwi[week-2]?.monthName : null;
    return currentMonth !== prevMonth;
  });
  
  const xAxisGroup = g.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${innerHeight})`);
    
  xAxisGroup.call(d3.axisBottom(xScale)
    .tickValues(monthTicks)
    .tickFormat(d => {
      const index = Math.round(d) - 1;
      if (index >= 0 && index < fwi.length) {
        const currentMonth = fwi[index].monthName;
        const prevMonth = index > 0 ? fwi[index-1].monthName : null;
        return currentMonth !== prevMonth ? currentMonth : "";
      }
      return "";
    })
    .tickSizeOuter(0));
  xAxisGroup.select(".domain").attr("stroke", "currentColor");
  xAxisGroup.selectAll(".tick text")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("dy", "1.5em");
  
  // line
  const line = d3.line()
    .x(d => xScale(d.week))
    .y(d => yScale(d.fwi));
    
  g.append("path")
    .datum(fwi)
    .attr("fill", "none")
    .attr("stroke", "black")
    .attr("stroke-width", Math.max(1.5, Math.min(3, width / 400)))
    .attr("d", line);
  
  // invisible dots for tooltips
  g.selectAll(".dot")
    .data(fwi)
    .enter().append("circle")
    .attr("cx", d => xScale(d.week))
    .attr("cy", d => yScale(d.fwi))
    .attr("r", 3)
    .attr("fill", "transparent")
    .style("cursor", "default")
    .on("mouseover", function(event, d) {
      d3.selectAll(".d3-tooltip").remove();
      
      // determine risk category
      const fwiValue = d.fwi;
      const riskCategory = riskCategories.find(cat => 
        fwiValue >= cat.min && fwiValue < cat.max
      ) || riskCategories[riskCategories.length - 1];

      const tooltip = d3.select("body").append("div")
        .attr("class", "d3-tooltip")
        .style("position", "absolute")
        .style("background", "white")
        .style("color", "black")
        .style("padding", "8px 12px")
        .style("border", "1.8px solid #000000")
        .style("font-family", "system-ui")
        .style("font-size", "12px")
        .style("font-weight", "normal")
        .style("line-height", "1.4")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000")
        .style("opacity", 0);
        
      tooltip.html(`<div>Month: ${d.monthName}</div><div>FWI: ${fwiValue.toFixed(2)}</div><div>Risk Level: ${riskCategory.name}</div><div>&nbsp;</div><div style="font-style: italic;">Only 5% of ${d.monthName} days exceeded this level</div>`)
        .style("left", (event.pageX - 80) + "px")
        .style("top", (event.pageY - 100) + "px")
        .transition()
        .duration(200)
        .style("opacity", 1);
    })
    .on("mousemove", function(event) {
      const tooltip = d3.select(".d3-tooltip");
      if (!tooltip.empty()) {
        tooltip
          .style("left", (event.pageX - 80) + "px")
          .style("top", (event.pageY - 100) + "px");
      }
    })
    .on("mouseout", function() {
      d3.selectAll(".d3-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
    });
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Fire Weather Index (FWI), January - December");
  
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(cityName);
  
  // caption (wrapped text)
  const captionText = "Data: NASA Global Fire Weather Database (GFWED) | Risk Classification: EFFIS/Copernicus Emergency Management Service | Note: Thresholds represent international standard; regional variation may apply";
  const captionLines = wrapText(captionText, width - 40, "10px system-ui");
  
  captionLines.forEach((line, i) => {
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 35 + (i * 12))
      .attr("text-anchor", "start")
      .attr("fill", "#666")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .text(line);
  });
  
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);

  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 45)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", "11px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
  return svg.node();
}


// ------------------------------------------------------------
// plot_fwi_d
// ------------------------------------------------------------
function plot_fwi_d(fwi, {
  cityName = globalCity,
  width = plotWidth,
  yLabel = "Danger Level",
  xLabel = "Weeks",
  showPercentages = true
} = {}) {
  
  const height = width * heightRatio;
  const scaleFactor = width / 800;
  const minScale = 0.6;
  const maxScale = 1.5;
  const dynamicScale = Math.max(minScale, Math.min(maxScale, scaleFactor));
  
  const margin = {
    top: 90,
    right: Math.max(180, width * 0.25, 180 * dynamicScale),
    bottom: Math.max(110, width * 0.12, 50 * dynamicScale),
    left: Math.max(150, width * 0.15, 120 * dynamicScale)
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // count occurrences of each danger level
  const dangerCounts = d3.rollup(fwi, v => v.length, d => d.danger);
  
  // define all possible danger levels in order
  const allDangerLevels = [
    "Extreme Risk", "Very High Risk", "High Risk", "Moderate Risk", "Low Risk", "Very Low Risk"
  ];
  
  // danger mapping
  const dangerMapping = {
    "Extreme Risk": "Extreme",
    "Very High Risk": "Very high",
    "High Risk": "High",
    "Moderate Risk": "Moderate",
    "Low Risk": "Low",
    "Very Low Risk": "Very low"
  };
  
  // data array with counts and percentages
  const distributionData = allDangerLevels.map(level => ({
    danger: level,
    count: dangerCounts.get(dangerMapping[level]) || 0,
    percentage: ((dangerCounts.get(dangerMapping[level]) || 0) / fwi.length * 100)
  }));
  
  // color mapping for danger levels
  const colorMap = {
    "Extreme Risk": "#8B0000",
    "Very High Risk": "#F44336",
    "High Risk": "#FF9800",
    "Moderate Risk": "#FFC107",
    "Low Risk": "#8BC34A",
    "Very Low Risk": "#4CAF50"
  };
  
  // calculate domain max
  const maxCount = Math.max(...distributionData.map(d => d.count));
  const tickStep = Math.ceil(maxCount / 10) || 1;
  const lastTick = Math.ceil(maxCount / tickStep) * tickStep;
  const domainMax = lastTick;
  
  // scales
  const xScale = d3.scaleLinear()
    .domain([0, domainMax])
    .range([0, innerWidth]);
  
  const yScale = d3.scaleBand()
    .domain(allDangerLevels)
    .range([0, innerHeight])
    .padding(0.2);
  
  // svg
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "white")
    .style("font", Math.max(12, Math.min(18, 14 * dynamicScale)) + "px system-ui");
  
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // grid lines (grey)
  const xAxisGrid = d3.axisBottom(xScale)
    .ticks(Math.max(4, Math.min(10, Math.floor(innerWidth / 80))))
    .tickSize(innerHeight)
    .tickFormat("");
  
  g.append("g")
    .attr("class", "grid")
    .call(xAxisGrid)
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll(".tick line")
      .attr("stroke", "#f0f0f0")
      .attr("stroke-opacity", 1)
      .attr("stroke-width", 1));
  
  // background "dummy" bars
  g.selectAll(".dummy-bar")
    .data(distributionData)
    .enter().append("rect")
    .attr("class", "dummy-bar")
    .attr("x", 0)
    .attr("y", d => yScale(d.danger))
    .attr("width", xScale(domainMax))
    .attr("height", yScale.bandwidth())
    .attr("fill", "#f8f9fa")
    .attr("fill-opacity", 0.3)
    .attr("stroke", "#dee2e6")
    .attr("stroke-width", Math.max(0.5, 1 * dynamicScale));
  
  // actual data bars
  g.selectAll(".data-bar")
    .data(distributionData.filter(d => d.count > 0))
    .enter().append("rect")
    .attr("class", "data-bar")
    .attr("x", 0)
    .attr("y", d => yScale(d.danger))
    .attr("width", d => xScale(d.count))
    .attr("height", yScale.bandwidth())
    .attr("fill", d => colorMap[d.danger])
    .attr("fill-opacity", 0.40)
    .attr("stroke", "white")
    .attr("stroke-opacity", 0.3)
    .attr("stroke-width", Math.max(0.5, 1 * dynamicScale));
  
  // text labels (positioned outside the bars for readability)
  g.selectAll(".label")
    .data(distributionData)
    .enter().append("text")
    .attr("class", "label")
    .attr("x", xScale(domainMax) + 10)
    .attr("y", d => yScale(d.danger) + yScale.bandwidth() / 2)
    .attr("text-anchor", "start")
    .attr("dominant-baseline", "middle")
    .attr("fill", d => d.count > 0 ? "black" : "#6c757d")
    .attr("font-size", Math.max(9, Math.min(13, 11 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("font-style", d => d.count > 0 ? "normal" : "italic")
    .text(d => d.count > 0 ?
      (showPercentages ? `${d.count} weeks (${d.percentage.toFixed(1)}%)` : `${d.count} weeks`) :
      "0 weeks (0.0%)");
  
  // y-axis with wrapped text labels
  const yAxisGroup = g.append("g");
  yAxisGroup.call(d3.axisLeft(yScale)
    .tickSize(0)
    .tickPadding(10));
  yAxisGroup.select(".domain").remove();
  
  // Replace text with wrapped text
  yAxisGroup.selectAll(".tick text").remove();
  yAxisGroup.selectAll(".tick")
    .append("foreignObject")
    .attr("width", margin.left - 15)
    .attr("height", yScale.bandwidth())
    .attr("x", -(margin.left - 5))
    .attr("y", -yScale.bandwidth() / 2)
    .append("xhtml:div")
    .style("width", (margin.left - 15) + "px")
    .style("height", yScale.bandwidth() + "px")
    .style("display", "flex")
    .style("align-items", "center")
    .style("justify-content", "flex-end")
    .style("font-size", Math.max(10, Math.min(14, 12 * dynamicScale)) + "px")
    .style("font-family", "system-ui")
    .style("text-align", "right")
    .style("line-height", "1.2")
    .html(d => d);
  
  // x-axis
  const xAxisGroup = g.append("g")
    .attr("transform", `translate(0,${innerHeight})`);
  xAxisGroup.call(d3.axisBottom(xScale)
    .ticks(Math.max(4, Math.min(10, Math.floor(innerWidth / 80))))
    .tickSize(Math.max(3, 6 * dynamicScale))
    .tickSizeOuter(0));
  xAxisGroup.select(".domain").attr("stroke", "currentColor");
  xAxisGroup.selectAll(".tick text")
    .attr("font-size", Math.max(10, Math.min(14, 12 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("dy", "1.5em");
  
  // title
  svg.append("text")
    .attr("x", 20)
    .attr("y", 25)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "18px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text("Fire Weather Index (FWI) Danger Level Distribution");
  
  // subtitle
  svg.append("text")
    .attr("x", 20)
    .attr("y", 45)
    .attr("text-anchor", "start")
    .attr("fill", "currentColor")
    .attr("font-size", "16px")
    .attr("font-family", "system-ui")
    .attr("font-style", "italic")
    .attr("font-weight", "normal")
    .text(`${cityName} (${fwi.length}-week period)`);
  
  // caption (wrapped text)
  const captionText = "Data: NASA Global Fire Weather Database (GFWED) | Risk Classification: EFFIS/Copernicus Emergency Management Service | Note: Thresholds represent international standard; regional variation may apply";
  const captionLines = wrapText(captionText, width - 40, "10px system-ui");
  
  captionLines.forEach((line, i) => {
    svg.append("text")
      .attr("x", 20)
      .attr("y", height - 35 + (i * 12))
      .attr("text-anchor", "start")
      .attr("fill", "#666")
      .attr("font-size", "10px")
      .attr("font-family", "system-ui")
      .text(line);
  });
  
  // y-axis label
  svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 20)
    .attr("x", -(margin.top + innerHeight/2))
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", Math.max(11, Math.min(16, 13 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(yLabel);
  
  // x-axis label
  svg.append("text")
    .attr("x", margin.left + innerWidth/2)
    .attr("y", height - 75)
    .attr("text-anchor", "middle")
    .attr("fill", "currentColor")
    .attr("font-size", Math.max(11, Math.min(16, 13 * dynamicScale)) + "px")
    .attr("font-family", "system-ui")
    .attr("font-weight", "normal")
    .text(xLabel);
  
  return svg.node();
}



// ------------------------------------------------------------
// Exports
// ------------------------------------------------------------
export {
  // Helper functions
  wrapText,
  calculateAgeDependencyRatios,
  parseRwiCategory,
  parseUbaAreaRange,
  parsePvAreaRange,
  parseAirQualityRange,
  parseSummerRange,
  parseNdviRange,
  parseElevationRange,
  parseSlopeRange,
  parseLsAreaRange,
  parseLAreaRange,
  // Plot functions
  plot_pga,
  plot_pgp,
  plot_pas,
  plot_pas_pyramid,
  plot_age,
  plot_dependency,
  plot_rwi_area,
  plot_uba_area,
  plot_ubaa,
  plot_ubap,
  plot_lc,
  plot_uddm,
  plot_pv_area,
  plot_pv_alt,
  plot_pv_d,
  plot_pv,
  plot_aq,
  plot_summer_area,
  plot_ndvi_area,
  plot_fe,
  plot_fu,
  plot_pu,
  plot_cu,
  plot_comb,
  plot_e,
  plot_s,
  plot_ls_area,
  plot_l_area,
  plot_fwi,
  plot_fwi_d,
  // Variables
  plotWidth
};

// Default export with init - use: import p from "./ojs/plots.js"
export default function() {
  return {
    plot_pga, plot_pgp, plot_pas, plot_pas_pyramid, plot_age, plot_dependency,
    plot_rwi_area, plot_uba_area, plot_ubaa, plot_ubap, plot_lc, plot_uddm,
    plot_pv_area, plot_pv_alt, plot_pv_d, plot_pv, plot_aq, plot_summer_area,
    plot_ndvi_area, plot_fe, plot_fu, plot_pu, plot_cu, plot_comb,
    plot_e, plot_s, plot_ls_area, plot_l_area, plot_fwi, plot_fwi_d
  };
}
