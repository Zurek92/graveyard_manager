function showElement(elementId, itemFunc){
    var element = document.getElementById(elementId);
    element.style.display='block';
    itemFunc.removeEventListener('click', function(){showElement(elementId, itemFunc);});
    itemFunc.addEventListener('click', function(){hideElement(elementId, itemFunc);});
}

function hideElement(elementId, itemFunc){
    var element = document.getElementById(elementId);
    element.style.display='none';
    itemFunc.addEventListener('click', function(){showElement(elementId, itemFunc);});
    itemFunc.removeEventListener('click', function(){hideElement(elementId, itemFunc);});
}
