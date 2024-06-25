let total_amount = 0;
let lista = [];
let webpay_total = 0;

function comprarProducto() { 
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    let productos = [];

    cart.forEach(item => {
        for (let i = 0; i < item.count; i++) {
            productos.push(item.product);
        }
    });

    document.getElementById('webpay_total').value = total_amount;
    document.getElementById('nombre_producto').value = productos.join(',');
    document.getElementById('paymentForm').submit();
}


function guardarSeleccion() {
    var select = document.getElementById("conversion");
    var valorSeleccionado = select.value;
    localStorage.setItem("conversionSeleccionada", valorSeleccionado);
}

document.addEventListener('DOMContentLoaded', function() {
    var valorGuardado = localStorage.getItem("conversionSeleccionada");
    if (valorGuardado) {
        var select = document.getElementById("conversion");
        select.value = valorGuardado;
    } else {
        select.value = 'clp';
    }
    displayCart();
});

function addToCart(product, price, quantityId) {
    let quantityInput = document.getElementById(quantityId);
    let quantity = parseInt(quantityInput.value);

    if (isNaN(quantity) || quantity < 1) {
        quantity = 1; // Establecer la cantidad predeterminada en 1 si no es válida
    }

    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    // Verificar si el producto ya está en el carrito
    let productInCart = cart.find(item => item.product === product);
    if (productInCart) {
        productInCart.count += quantity;
    } else {
        cart.push({ product, price: parseFloat(price), count: quantity });
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    displayCart();
}


// Función para mostrar los productos del carrito
function displayCart() {
    let total = 0;
    let webpay_total = 0;
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    let cartList = document.getElementById('cart');
    cartList.innerHTML = '';

    cart.forEach((item, index) => {
        if (!item.price) return; // Saltar si el precio no está definido
        let convertedPrice = item.price / valor_conversion;
        let listItem = document.createElement('li');

        if (!tipo_divisa) {
            listItem.textContent = `x${item.count} ${item.product} - $${(convertedPrice * item.count).toFixed(2)}`;
        } else if (tipo_divisa === 'dolar') {
            listItem.textContent = `x${item.count} ${item.product} - $${(convertedPrice * item.count).toFixed(2)}`;
        } else {
            listItem.textContent = `x${item.count} ${item.product} - ${(convertedPrice * item.count).toFixed(2)}€`;
        }

        let removeButton = document.createElement('button');
        removeButton.textContent = 'Eliminar';
        removeButton.onclick = function() { removeFromCart(index); };
        listItem.appendChild(removeButton);
        cartList.appendChild(listItem);

        total += convertedPrice * item.count;
        webpay_total += item.price * item.count;
    });

    total_amount = webpay_total;
    if (!tipo_divisa) {
        document.getElementById('total').textContent = total.toFixed(2);
    } else {
        document.getElementById('total').textContent = total.toFixed(2);
    }
    document.getElementById('webpay_total').value = total_amount;
    document.getElementById('amount').value = total.toFixed(2);
}

// Función para eliminar productos del carrito
function removeFromCart(index) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    if (cart[index].count > 1) {
        cart[index].count -= 1;
    } else {
        cart.splice(index, 1);
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    displayCart();
}

function clearLocalStorage() {
    localStorage.removeItem('cart');
    localStorage.removeItem('conversionSeleccionada');
    lista = [];
}

function clearCart() {
    localStorage.removeItem('cart');
    lista = [];
    displayCart();
}



