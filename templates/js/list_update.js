{% if selected_table is defined %}
<script>
    var updateLocal = function(pk) {
        $.ajax({
            url: "{{ url_for('record_get', table=selected_table)}}",
            data: {'pk':pk}
        }).done(function(data) {
            $tds = $("tr[data-pk=" + pk + "]").find('td');
            for (var i = 0; i < data.length; i++) {
                $($tds[i]).text(data[i]);
            }
            console.log('----------------------');
            console.log(data);
        });
    };


    var lastUpdated = {{ last_update }};
    var checkForUpdate = function () {
        pks = [];

        $('.entry').each(function(index, elem) {
            pks.push($(elem).data('pk'));
        });

        $.ajax({
            url: "{{url_for('get_log', table=selected_table)}}",
            method: "GET",
            traditional:true,
            data: {
                'last_update': lastUpdated,
                pk: pks
            },
        }).done(function(data) {
            lastUpdated = data['last_update'];
            console.log('done');
            console.log(data);

            for (var i=0; i < pks.length; i++) {
                if (data['changes'][pks[i]]  !== undefined) {
                    var status = data['changes'][pks[i]];
                    if (status === 'MODIFIED') {
                        $("tr[data-pk=" + pks[i] + "]").addClass('bg-warning');
                        updateLocal(pks[i]);
                    } else if (status === 'DELETED') {
                        $("tr[data-pk=" + pks[i] + "]").addClass('bg-danger');
                    }
                }
            }

        });
    };
    setInterval(checkForUpdate, 3000);

</script>
{% endif %}