<script>
$(document).ready(function () {
    var table = '{{ table }}';
    var checkForUpdate = function() {
        fields = []
        $('.edit_form').find('.edit-input').each(function() {fields.push($(this).attr('name'))})
        console.log(table);
    }

    setInterval(checkForUpdate, 2000)
});
</script