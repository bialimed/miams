/*
# Copyright (C) 2018 IUCT-O
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
function sortNumber(a,b) {
    return a - b;
}

String.prototype.capitalize = function() {
    return this.replace(/(?:^|\s)\S/g, function(a) { return a.toUpperCase(); });
};


function selectSample( spl_data, pre_zoom_min=null, pre_zoom_max=null ){
	fillSample('sample-summary', spl_data)
	drawSizeGraph('length-graph', spl_data["loci"], pre_zoom_min, pre_zoom_max)
	drawTable('nb-seq-table', spl_data["loci"])
}

function navButtonUpdate(select_spl){
	const curr_idx = select_spl.prop('selectedIndex')
	if(curr_idx == Object.keys(data_by_spl).length - 1){
		$("#next-spl").addClass("disabled")
	} else {
		$("#next-spl").removeClass("disabled")
	}
	if(curr_idx == 0){
		$("#prev-spl").addClass("disabled")
	} else {
		$("#prev-spl").removeClass("disabled")
	}
}

function fillSample( container_id, data ){
	const status = data["sample"]["is_stable"] == null ? "unknown" : (data["sample"]["is_stable"] ? "stable" : "instable")
	$("#" + container_id + " #spl-status").text(status.capitalize())
	$("#" + container_id + " #spl-status").removeClass("status-stable status-unknown status-instable")
	$("#" + container_id + " #spl-status").addClass("status-" + status)
	$("#" + container_id + " #spl-score").text(data["sample"]["score"])
	let loci_metrics = {
		"nb_undefined": 0,
		"nb_instable": 0,
		"nb_stable": 0
	}
	const loci_ids = Object.keys(data["loci"]).sort()
	loci_ids.forEach(function (key) {
		const locus = data["loci"][key]
		if(locus["is_stable"] == null){
			loci_metrics["nb_undefined"] += 1
		} else if(locus["is_stable"]){
			loci_metrics["nb_stable"] += 1
		} else {
			loci_metrics["nb_instable"] += 1
		}
	})
	$("#" + container_id + " #spl-stable-loci").text(
		loci_metrics["nb_stable"] + "/" + loci_ids.length
	)
	$("#" + container_id + " #spl-instable-loci").text(
		loci_metrics["nb_instable"] + "/" + loci_ids.length
	)
	$("#" + container_id + " #spl-unknown-loci").text(
		loci_metrics["nb_undefined"] + "/" + loci_ids.length
	)
}

function drawSizeGraph( container_id, data, pre_zoom_min=null, pre_zoom_max=null ){
	// Transforms data to series
	let series = []
	const loci_ids = Object.keys(data).sort()
	loci_ids.forEach(function (key) {
		const locus = data[key]
		const nb_by_lengths = locus["pairs_combination"]["nb_by_lengths"]
		const lengths = Object.keys(nb_by_lengths).sort(sortNumber)
        // Set series
		let series_data = []
		lengths.forEach(function (key) {
			series_data.push([parseInt(key), nb_by_lengths[key]])
		})
		series.push({
			"name": locus["name"],
			"data": series_data
		})
	})
	// Draws graph
	Highcharts.chart(
		container_id,
		{
			chart: {
				type: "column",
				zoomType: "x",
                events: {
                    load: function(){
                        if(pre_zoom_min != null || pre_zoom_max != null){
                            this.xAxis[0].setExtremes(pre_zoom_min, pre_zoom_max)
                            this.showResetZoom()
                        }
                    }
                }
			},
			title: {
				text: 'Fragments lengths'
			},
			xAxis: {
				tickInterval: 1,
				title: {
					text: "Length"
				}
			},
			yAxis: {
				title: {
					text: "Nb amplicons"
				}
			},
            tooltip: {
                crosshairs: [true],
                shared: true,
                formatter: function() {
                    let lines = ['Nb amplicons for <b>' + this.points[0].x + 'nt</b>:']
                    $.each(this.points, function(idx, point) {
                        lines.push(
                            '<b><span style="color:' + point.series.color + '">' + point.series.name + '</b></span>' +
                            ': ' +
                            '<b>' + point.y + '</b>'
                        )
                    });
                    return lines.join('<br />')
                }
            },
			credits: {
				enabled: false
			},
			series: series
		},
		/*function(e){ // Redraw chart to prevent problem with scrollbar
			setTimeout(function() {
				const container = $("#" + container_id)
				e.setSize(container.width(), container.height());
			}, 1)
		}*/
	);
}

function drawTable( container_id, data ){
    // Prepare data
    const loci_ids = Object.keys(data).sort()
    let rows_data = new Array()
    loci_ids.forEach(function (key) {
        const locus = data[key]
        const status = (locus["is_stable"] == null ? "unknown" : (locus["is_stable"] ? "stable" : "instable"))
        const nb_pairs_combined = locus["pairs_combination"]["nb_pairs"]
        rows_data.push([
            locus["position"],
            locus["name"],
            status,
            locus["nb_pairs"],
            (nb_pairs_combined*100/locus["nb_pairs"]).toFixed(2)
        ])
    });
    // Create/Clear datatable
    $("#" + container_id).removeClass("d-none")
    let datatable = $("#" + container_id).DataTable()
    datatable.clear()
    // Add data
    datatable.rows.add(rows_data)
    // Add class on status cells
    datatable.columns(2).nodes()
        .flatten()
        .to$()
        .each( function (idx, td) {
            td.className = 'sticker status-' + td.textContent
        })
    // Draw
    datatable.draw()
}
