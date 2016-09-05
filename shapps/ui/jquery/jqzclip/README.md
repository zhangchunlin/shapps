sample:
=============================
HTML:
-----------------------------
```
<div class="row-fluid" style='position:relative'>
    <div style="float:left"  >MOTO Path=  <a ms-href="https://artifacts-test.mot.com/artifactory/xfer_scratch/{%el.moto_path%}" target="_blank" ms-attr-id="moto_path_{%$index%}">{%el.moto_path%}</a></div>
    <div style="float:left" data-toggle="tooltip" data-placement="top" title="Copy to Clipboard"><a ms-attr-id="{%$index%}" href="#" class="moto_path_a"><span>📋</span></a></div>
</div>
```

JS:
-----------------------------
```
$(this).zclip({
    path: '/static/jqzclip/ZeroClipboard.swf',
    copy: function() {
        return "https://artifacts-test.mot.com/artifactory/xfer_scratch/"+$('#moto_path_'+$(this).attr('id')).html();
    },
    afterCopy : function(){
    }
});
```
