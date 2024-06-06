let total_amount = 0;
function comprarProducto() { 
    document.getElementById('amount').value = total_amount;
    document.getElementById('paymentForm').submit();
}
function guardarSeleccion() {
    var select = document.getElementById("conversion");
    var valorSeleccionado = select.value;
    localStorage.setItem("conversionSeleccionada", valorSeleccionado);
}
window.onload = function() {
    var valorGuardado = localStorage.getItem("conversionSeleccionada");
    if (valorGuardado) {
        var select = document.getElementById("conversion");
        select.value = valorGuardado;
    }
}

function addToCart(product, price) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.push({ product, price: parseFloat(price) });
    localStorage.setItem('cart', JSON.stringify(cart));
    displayCart();
}

// Función para mostrar los productos del carrito
function displayCart() {
    let total = 0;
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    let cartList = document.getElementById('cart');
    cartList.innerHTML = '';
    cart.forEach((item, index) => {
        if (!item.price) return; // Saltar si el precio no está definido
        let listItem = document.createElement('li');
        listItem.textContent = `${item.product} - $${item.price.toFixed(2)}`;
        let removeButton = document.createElement('button');
        removeButton.textContent = 'Eliminar';
        removeButton.onclick = function() { removeFromCart(index); };
        listItem.appendChild(removeButton);
        cartList.appendChild(listItem);
        total += item.price;
    });
    total_amount = total;
    document.getElementById('total').textContent = total.toFixed(2);
    document.getElementById('amount').value = total.toFixed(2);
}

// Función para eliminar productos del carrito
function removeFromCart(index) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    displayCart();
}

// Mostrar el carrito al cargar la página
window.onload = displayCart;





