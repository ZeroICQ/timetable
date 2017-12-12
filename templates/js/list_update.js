{% if selected_table is defined %}
<script>
//    var updateLocal = function(pk) {
//        $.ajax({
//            {#url: "{{ url_for('record_get', table=selected_table)}}",#}
//            data: {'pk':pk}
//        }).done(function(data) {
//            $tds = $("tr[data-pk=" + pk + "]").find('td');
//            for (var i = 0; i < data.length; i++) {
//                $($tds[i]).text(data[i]);
//            }
//            console.log('----------------------');
//            console.log(data);
//        });
//    };
//
//


    var updateTable = function(data, pks) {
        console.log(data);
        for (var i = 0; i < pks.length; i++) {
            var status = data.statuses[pks[i]]
            var row = $("tr[data-pk=" + pks[i] + "]")
            if (status === 'MODIFIED') {
                row.find('td').each(function() {
                    newValue = data.values[pks[i]][$(this).data('col-name')]
                    $(this).text(newValue || 'None')
                });
            } else if (status === 'DELETED') {
                row.remove();
            }
        }
    };

    var lastUpdated = {{ last_update }};
    var checkForUpdate = function () {
        pks = [];

        $('.entry').each(function(index, elem) {
            pks.push($(elem).data('pk'));
        });

        $.ajax({
            url: "{{ url_for('get_log', table=selected_table) }}",
            method: "GET",
            traditional: true,
            data: {
                pk: pks,
                'last_update': lastUpdated,
            },
            success: function(data) {
                lastUpdated = data['last_update'];
                updateTable(data, pks);
            },
        });
//
//        $.ajax({
//            {#url: "{{url_for('get_log', table=selected_table)}}",#}
//            method: "GET",
//            traditional:true,
//            data: {
//                'last_update': lastUpdated,
//                pk: pks
//            },
//        }).done(function(data) {
//            lastUpdated = data['last_update'];
//            console.log('done');
//            console.log(data);
//
//            for (var i=0; i < pks.length; i++) {
//                if (data['changes'][pks[i]]  !== undefined) {
//                    var status = data['changes'][pks[i]];
//                    if (status === 'MODIFIED') {
//                        $("tr[data-pk=" + pks[i] + "]").addClass('bg-info');
//                        updateLocal(pks[i]);
//                    } else if (status === 'DELETED') {
//                        $("tr[data-pk=" + pks[i] + "]").addClass('bg-danger');
//                    }
//                }
//            }
//
//        });
    };
    setInterval(checkForUpdate, 3000);
    $('#debugich').click(checkForUpdate);
</script>
{% endif %}
