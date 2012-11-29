//jQuery(function($){


	function isInCircle(x, y) {
			var relative_x = x - this.x;
			var relative_y = y - this.y;
			return Math.sqrt(relative_x*relative_x + relative_y*relative_y) <= this.r;
	}
	
	function isInRectangle(x, y) {
			return (this.x1 <= x && x <= this.x2) && (this.y1 <= y && y<= this.y2);
	}
	
	function getCircleCenter() { return {x: this.x, y: this.y}; }
	
	function getRectangleCenter() { return {x: (this.x2+this.x1)/2, y: (this.y2+this.y1)/2}; }
	
	var objects = [];

	function whereIam(x, y) {
			for (var i=0; i<objects.length; i++) {
					var obj = objects[i];
					if (obj.isInObject(x, y))
							return obj;
			}
					
			return null;
	}
	
	function showMiejsce(a) {
		$.each(objects, function(i, object) {
			if (object.id == a) {
				var center = object.getCenter();
				var offset = viewer.iviewer('imageToContainer', center.x, center.y);
				var containerOffset = viewer.iviewer('getContainerOffset');
				var pointer = $('#pointer' + object.id);
				var wrapper = $('.wrapper');
				if((offset.x-(pointer.width()/2)) < 0 || (offset.y-pointer.height()) <0 || offset.x+(pointer.width()/2) > wrapper.width() || offset.y >wrapper.height() ){
						pointer.css('display', 'none');
				} else {
						pointer.css('display', 'block');
				}
				//offset.x += containerOffset.left - 20;
				//offset.y += containerOffset.top - 40;
				offset.x += containerOffset.left - 11;   // 19 to jest szerokosc - 8
				offset.y += containerOffset.top - 32;
				//pointer.css('display', 'block');
				pointer.css('left', offset.x+'px');
				pointer.css('top', offset.y+'px');
				//alert("x: " + offset.x + ", y: " + offset.y);
			}                    
		});
	}
	function showKategoria(a){
		$.each(objects, function(i, object) {
			if (object.kategoria == a) {
				var center = object.getCenter();
				var offset = viewer.iviewer('imageToContainer', center.x, center.y);
				var containerOffset = viewer.iviewer('getContainerOffset');
				var pointer = $('#pointer' + object.id);
				var wrapper = $('.wrapper');
				if((offset.x-(pointer.width()/2)) < 0 || (offset.y-pointer.height()) <0 || offset.x+(pointer.width()/2) > wrapper.width() || offset.y >wrapper.height() ){
						pointer.css('display', 'none');
				} else {
						pointer.css('display', 'block');
				}
				//offset.x += containerOffset.left - 20;
				//offset.y += containerOffset.top - 40;
				offset.x += containerOffset.left - 11;   // 19 to jest szerokosc - 8
				offset.y += containerOffset.top - 32;
				pointer.css('left', offset.x+'px');
				pointer.css('top', offset.y+'px');
			}                    
		});
	}
	
	window.show = show;

function wylaczWszystkie(){
	reg = /^pointer.*$/;
	$('[id^=pointer]').css('display', 'none');
}


