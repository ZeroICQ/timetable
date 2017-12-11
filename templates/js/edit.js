<script>
$(document).ready(function () {
    var table = '{{ table }}';

    var lastUpdated = {{ last_update }};

    var changeStatus = function(status) {
        if (status === 'DELETED') {
            $('#modify-alert').slideUp('medium');
            $('#delete-alert').slideDown('medium');
        } else if (status === 'MODIFIED') {
            $('#modify-alert').slideDown('medium');
            $('#delete-alert').slideUp('medium');
        }
    }

    var checkForUpdate = function() {
//        fields = []
//        $('.edit_form').find('.edit-input').each(function() {fields.push($(this).attr('name'))})
//        console.log(table);

        $.ajax({
            url: "{{url_for('record_get', table=table, pk=pk)}}",
            method: "GET",
            traditional:true,
            data: {
                'last_update': lastUpdated,
            },
            success: function(data) {
                lastUpdated = data['last_update'];
                console.log(data);
                changeStatus(data.status);
            },
        });
    }

    setInterval(checkForUpdate, 5000);
    checkForUpdate();
});
</script