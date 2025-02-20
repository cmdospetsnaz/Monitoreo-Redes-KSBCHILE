$(document).ready(function() {
    // Crear el mapa de Leaflet
    var map = L.map('map').setView([-35.675147, -71.542969], 5);

    // Añadir la capa de mapa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Coordenadas, direcciones, teléfonos y correos manuales
    var cityMarkers = {
        "Antofagasta": {
            coords: [-23.698168, -70.419235],
            address: "Avenida de la Minería 265, La Negra Antofagasta",
            phone: "+56 55 263 8900",
            email: "cl.anfofagasta@ksb.com"
        },
        "Coquimbo": {
            coords: [-29.971910, -71.274651],
            address: "Calle Nueva Dos 1251, Barrio Industrial Coquimbo",
            phone: "+56 51 223 9714",
            email: "cl.coquimbo@ksb.com"
        },
        "Concepción": {
            coords: [-36.799877, -73.073631],
            address: "Vasco Nuñez de Balboa 9060, Parque Industrial San Andrés Concepción",
            phone: "+56 41 240 8000",
            email: "cl.concepcion@ksb.com"
        },
        "Temuco": {
            coords: [-38.767284, -72.613220],
            address: "Camino A Aeropuerto Maquehue 3081, Bodega N°4, Work Center Maquehue Temuco",
            phone: "+56 45 225 4545",
            email: "cl.temuco@ksb.com"
        },
        "Puerto Montt": {
            coords: [-41.472698, -72.994904],
            address: "Ruta 5 Sur 1025, Megacentro 2, Bodega 12 Puerto Montt",
            phone: "+56 65 231 3000",
            email: "cl.ptomontt@ksb.com"
        },
        "Santiago": {
            coords: [-33.347729, -70.711838],
            address: "Las Esteras Sur 2851, Quilicura Santiago",
            phone: "+56 22 677 8300",
            email: "cl.ksb@ksb.com"
        }
    };

    function addCityMarkers() {
        for (var city in cityMarkers) {
            var marker = L.marker(cityMarkers[city].coords).addTo(map)
                .bindPopup(`SUCURSAL: ${city}`)
                .on('click', function(e) {
                    var cityName = e.target.getPopup().getContent().split(": ")[1];
                    var info = cityMarkers[cityName];
                    L.popup()
                        .setLatLng(e.latlng)
                        .setContent(
                            `<strong>SUCURSAL: ${cityName}</strong><br>Dirección: ${info.address}<br>Teléfono: ${info.phone}<br>Correo: ${info.email}`
                        )
                        .openOn(map);
                });
        }
    }

    addCityMarkers();

    function fetchStatus() {
        $.getJSON('/get_status', function(data) {
            let tableBody = $('#ip-table-body');
            tableBody.empty();
            data.forEach(function(ip_info) {
                let row = `<tr>
                    <td class="ip-cell" data-ip="${ip_info.IP}" data-status="${ip_info.Estado}" data-ciudad="${ip_info.Ciudad}">
                        ${ip_info.IP}
                    </td>
                    <td class="${ip_info.Estado == 'Caída' ? 'text-danger' : 'text-success'}">
                        <span class="status-icon" style="background-color: ${ip_info.Estado == 'Caída' ? 'red' : 'green'};"></span>
                        <span class="status-text">${ip_info.Estado}</span>
                    </td>
                    <td>${ip_info.Region}</td>
                    <td>${ip_info.Ciudad}</td>
                    <td>${ip_info.Pais}</td>
                    <td>${ip_info.HostName}</td>
                    <td>${ip_info.Hora}</td>
                    <td class="text-center">
                        <span class="location-icon" data-ciudad="${ip_info.Ciudad}" style="cursor: pointer;">
                            <img src="/static/icons/location.svg" alt="Ubicación" style="width: 50px; height: 50px;">
                        </span>
                    </td>
                </tr>`;
                tableBody.append(row);
            });

            // Agregar evento de clic a las celdas de IP para mostrar toast
            $('.ip-cell').click(function() {
                let ip = $(this).data('ip');
                let status = $(this).data('status');
                let ciudad = $(this).data('ciudad');
                showToast(ciudad, ip, status);
            });

            // Agregar evento de clic al ícono de ubicación para centrar el mapa y desplazar la página
            $('.location-icon').click(function() {
                let ciudad = $(this).data('ciudad');

                // Centrar el mapa en la ubicación correspondiente con más zoom
                if (cityMarkers[ciudad]) {
                    map.setView(cityMarkers[ciudad].coords, 17); // Ajusta el nivel de zoom según sea necesario
                }

                // Desplazar la página hacia el mapa
                $('html, body').animate({
                    scrollTop: $("#map").offset().top
                }, 1000);
            });
        });
    }

    function showToast(ciudad, ip, status) {
        let toastClass = status == 'Caída' ? 'bg-danger toast-caid' : 'bg-success';
        let iconPath = status == 'Caída' 
            ? '/static/icons/error.svg'
            : '/static/icons/success.svg';

        let toast = $(
            `<div class="toast ${toastClass}" role="alert" aria-live="assertive" aria-atomic="true" data-delay="${status == 'Caída' ? 40000 : 5000}">
                <div class="toast-header">
                    <strong class="mr-auto">Estado de la Red KSB</strong>
                    <small class="text-muted">Justo ahora</small>
                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="toast-body text-center">
                    <p>La red de "${ciudad}" con la IP "${ip}" está "${status}".</p>
                    <img src="${iconPath}" class="toast-icon" alt="Icono">
                </div>
            </div>`
        );

        $('.toast-container').empty().append(toast);
        toast.toast('show');
    }

    // Actualizar el estado cada 10 segundos
    setInterval(fetchStatus, 10000);

    // Mantener mostrando el toast cada 40 segundos
    setInterval(function() {
        $.getJSON('/get_status', function(data) {
            data.forEach(function(ip_info) {
                if (ip_info.Estado === 'Caída') {
                    showToast(ip_info.Ciudad, ip_info.IP, ip_info.Estado);
                }
            });
        });
    }, 40000);

    fetchStatus();
});
