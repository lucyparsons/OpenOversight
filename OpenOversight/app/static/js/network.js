function drawGraph(nodes_data,links_data) {
  //create somewhere to put the force directed graph
  var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");
    
  var radius = 7; 

  var simulation = d3.forceSimulation()
					.nodes(nodes_data);
                              
  var link_force =  d3.forceLink(links_data)
                        .id(function(d) { return d.id; });            
         
  var charge_force = d3.forceManyBody()
    .strength(-50)
    .distanceMin(80)
    .distanceMax(200); 
    
  var center_force = d3.forceCenter(width / 2, height / 2);  
                      
  simulation
    .force("charge_force", charge_force)
    .force("center_force", center_force)
    .force("links",link_force)
  ;
        
  //add tick instructions: 
  simulation.on("tick", tickActions );

  //add encompassing group for the zoom 
  var g = svg.append("g")
    .attr("class", "everything");

  //draw lines for the links 
  var link = g.append("g")
      .attr("class", "links")
    .selectAll("line")
    .data(links_data)
    .enter().append("line")
      .attr("stroke-width", 4);
      //.style("stroke", linkColour);        

  //draw circles for the nodes 
  var node = g.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(nodes_data)
        .enter()
        .append("circle")
        .attr("r", function(d) 
                    { d.weight = degree(d);
                      var minRadius = 1;
                      if(d.weight > 7)
                        d.weight = 7;
                      return minRadius + (d.weight);
                    });
        //.attr("fill", circleColour);

  node.append("title")
      .text(function(d) { return d.rank + " " + d.last + " #" + d.id; });


  //add drag capabilities  
  var drag_handler = d3.drag()
	.on("start", drag_start)
	.on("drag", drag_drag)
	.on("end", drag_end);	
	
  drag_handler(node);

  //add zoom capabilities 
  var zoom_handler = d3.zoom()
    .on("zoom", zoom_actions);

  zoom_handler(svg);

  //https://stackoverflow.com/questions/43906686/d3-node-radius-depends-on-number-of-links-weight-property
  function degree(d) {
    return link.filter(function(l) {
                          return l.source.id == d.id || l.target.id == d.id
                     }).size();
  }
 
  //Drag functions 
  //d is the node 
  function drag_start(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
  }

  //make sure you can't drag the circle outside the box
  function drag_drag(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
  }

  function drag_end(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  //Zoom functions 
  function zoom_actions(){
    g.attr("transform", d3.event.transform)
  }

  function tickActions() {
    //update circle positions each tick of the simulation 
    node
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; })
        //.attr("transform", function(d){return "translate("+d.x+","+d.y+")"});
    //update link positions 
    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });
  }

} 
