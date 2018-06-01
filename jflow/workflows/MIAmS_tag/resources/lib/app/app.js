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


function selectSample( spl_data, methods, models_peaks_by_locus=null, pre_zoom_min=null, pre_zoom_max=null ){
	fillSample('sample-summary', spl_data, "PairsCombi")
	drawSizeGraph('length-graph', spl_data.loci, "PairsCombi", models_peaks_by_locus, pre_zoom_min, pre_zoom_max)
	drawTable('nb-seq-table', spl_data.loci, methods)
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

function fillSample( container_id, data, method ){
	const status = data.results[method].status
	$("#" + container_id + " #spl-status").text(status.capitalize())
	$("#" + container_id + " #spl-status").removeClass("status-MSS status-MSI status-Undetermined")
	$("#" + container_id + " #spl-status").addClass("status-" + status)
	$("#" + container_id + " #spl-score").text(data.results[method].score)
	let loci_metrics = {
		"nb_undefined": 0,
		"nb_instable": 0,
		"nb_stable": 0
	}
	const loci_ids = Object.keys(data["loci"]).sort()
	loci_ids.forEach(function (key) {
		const locus_res = data.loci[key].results[method]
		if(locus_res.status == "Undetermined"){
			loci_metrics["nb_undefined"] += 1
		} else if(locus_res.status == "MSS"){
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

function ntile(data, step, nb_shunk=100){
    const sorted_data = data.sort(sortNumber)
    let data_idx = null
    let percentile_value = null
    if( step == 0 ){
        percentile_value = sorted_data[0]
    } else if( step == nb_shunk ){
        percentile_value = sorted_data[data.length - 1]
    } else {
        const data_idx = Math.ceil((step * sorted_data.length)/nb_shunk) - 1
        percentile_value = sorted_data[data_idx]
    }
    return percentile_value
}

function drawSizeGraph( container_id, data, method, models_peaks_by_locus=null, pre_zoom_min=null, pre_zoom_max=null ){
	// Transforms data to series
	let series = []
	let loci_idx = 0
	const loci_ids = Object.keys(data).sort()
	loci_ids.forEach(function (key) {
		const locus = data[key]
		const nb_by_length = locus.results[method].data["nb_by_length"]
		const lengths = Object.keys(nb_by_length).sort(sortNumber)
        // Set series
		let series_data = []
		lengths.forEach(function (key) {
			series_data.push([parseInt(key), nb_by_length[key]])
		})
		series.push({
			"name": locus.name,
			"data": series_data,
            "zIndex": 1,
            "colorIndex": loci_idx
        })
        if( models_peaks_by_locus != null ){
            const locus_peaks = models_peaks_by_locus[locus["position"]]
            series.push({
                "name": locus["name"] + " models higher peaks percentiles",
                "type": 'area',
                "linkedTo": ':previous',
                "fillOpacity": 0.3,
                "zIndex": 0,
                "colorIndex": loci_idx,
                "enableMouseTracking": false,
                "marker": {
                    enabled: false
                },
                "data": [
                    [ntile(locus_peaks, 0), 0],
                    [ntile(locus_peaks, 10), -50],
                    [ntile(locus_peaks, 90), -50],
                    [ntile(locus_peaks, 100), 0]
                ]
            })
            series.push({
                "name": locus["name"] + " models higher peaks median",
                "type": 'column',
                "linkedTo": ':previous',
                "zIndex": 0,
                "colorIndex": loci_idx,
                "borderColor": null,
                "enableMouseTracking": false,
                "marker": {
                    enabled: false
                },
                "data": [[ntile(locus_peaks, 50), -50]]
            })
        }
        loci_idx += 1
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

function getNbReads(method, result){
    let nb_reads = null
    if(method == "PairsCombi"){
        nb_reads = 0
        const lengths = Object.keys(result.data["nb_by_length"])
        lengths.forEach(function (curr_length) {
            nb_reads += result.data["nb_by_length"][curr_length]
        })
        nb_reads = nb_reads * 2
    } else if(method == "MSINGS"){
        nb_reads = 0
        result.data["peaks"].forEach(function (curr_peak) {
            nb_reads += curr_peak["DP"]
        })
    } else if(resuls.data.hasOwnProperty("nb_reads")){
        nb_reads = result.data["nb_reads"]
    }
    return nb_reads
}

function drawTable( container_id, data, methods ){
    // Prepare data
    let status_columns = []
    const loci_ids = Object.keys(data).sort()
    let rows_data = new Array()
    loci_ids.forEach(function (key) {
        const locus = data[key]
        let curr_row = [locus.position, locus.name]
        methods.forEach(function (curr_method) {
            curr_row = curr_row.concat([
                getNbReads(curr_method, locus.results[curr_method]),
                locus.results[curr_method].score,
                locus.results[curr_method].status
            ])
            status_columns.push(curr_row.length - 1)
        })
        rows_data.push(curr_row)
    });
    // Create/Clear datatable
    $("#" + container_id).removeClass("d-none")
    let datatable = $("#" + container_id).DataTable()
    datatable.clear()
    // Add data
    datatable.rows.add(rows_data)
    // Add class on status cells
    status_columns.forEach(function (col_idx) {
        datatable.columns(col_idx).nodes()
            .flatten()
            .to$()
            .each( function (idx, td) {
                td.className = 'sticker status-' + td.textContent
            })
    })
    // Draw
    datatable.draw()
}
