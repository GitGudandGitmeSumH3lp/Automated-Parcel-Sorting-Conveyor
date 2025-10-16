// app.js

// 1. Random Data Generation
const getRandomOrderID = () => {
  return Math.random().toString(36).substring(2, 10).toUpperCase();
};

const getRandomTrackingNumber = () => {
  return Math.floor(Math.random() * 1000000000).toString();
};

const getRandomBuyerName = () => {
  const names = ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown"];
  return names[Math.floor(Math.random() * names.length)];
};

const getRandomAddress = () => {
  const areas = [
    { barangay: "Muzon", district: ["North", "South", "Central"] },
    { barangay: "Tungko", district: ["Main", "Subdivision"] },
    { barangay: "Sapang Palay", district: ["West", "East"] },
    { barangay: "Santa Maria", district: ["City"] },
    { barangay: "Norzagaray", district: ["City"] }
  ];
  const selectedArea = areas[Math.floor(Math.random() * areas.length)];
  const street = `${Math.floor(Math.random() * 100)} St.`;
  const city = "San Jose del Monte";
  const province = "Bulacan";
  const zipCode = "1234";
  return {
    street,
    barangay: selectedArea.barangay,
    district: selectedArea.district[Math.floor(Math.random() * selectedArea.district.length)],
    city,
    province,
    zipCode
  };
};

const getRandomWeight = () => {
  return Math.floor(Math.random() * 7000); // Max 7kg
};

const getRandomQuantity = (weight) => {
  return Math.floor(weight / 500); // ~500g per item
};

// 2. RTS Sort Code Logic
const getRTSCode = (barangay, district) => {
  const rtsMap = {
    Muzon: {
      North: "RTS-BUL-SJDM-MZN1-A1",
      South: "RTS-BUL-SJDM-MZN2-A2",
      Central: "RTS-BUL-SJDM-MZN3-A3"
    },
    Tungko: {
      Main: "RTS-BUL-SJDM-TKM-B1",
      Subdivision: "RTS-BUL-SJDM-TKM-B2"
    },
    "Sapang Palay": {
      West: "RTS-BUL-SJDM-SPY1-C1",
      East: "RTS-BUL-SJDM-SPY2-C2"
    },
    "Santa Maria": "RTS-BUL-STM-SMR-D1",
    Norzagaray: "RTS-BUL-NRY-NRY-D2"
  };
  return rtsMap[barangay]?.[district] || "RTS-UNKNOWN";
};

// 3. Dynamic QR Code
const generateQRCode = (trackingNumber, containerId) => {
  new QRCode(document.getElementById(containerId), {
    text: `https://track.spx.com/${trackingNumber}`,
    width: 150,
    height: 150
  });
};

// 4. Image Export
const exportImage = (element, type) => {
  html2canvas(element, { scale: 3 }).then(canvas => {
    const link = document.createElement("a");
    link.download = `label_${getRandomOrderID()}.${type}`;
    link.href = canvas.toDataURL(`image/${type}`);
    link.click();
  });
};

// 5. UI Logic
document.getElementById("generateLabel").addEventListener("click", () => {
  const orderID = getRandomOrderID();
  const trackingNumber = getRandomTrackingNumber();
  const buyerName = getRandomBuyerName();
  const address = getRandomAddress();
  const weight = getRandomWeight();
  const quantity = getRandomQuantity(weight);

  const rtsCode = getRTSCode(address.barangay, address.district);

  const labelContainer = document.getElementById("shipping-label");
  labelContainer.innerHTML = `
    <table>
      <tr>
        <td>Order ID:</td><td>${orderID}</td>
      </tr>
      <tr>
        <td>Tracking Number:</td><td>${trackingNumber}</td>
      </tr>
      <tr>
        <td>Buyer Name:</td><td>${buyerName}</td>
      </tr>
      <tr>
        <td>Address:</td><td>${address.street}, ${address.barangay}, ${address.district}, ${address.city}, ${address.province}, ${address.zipCode}</td>
      </tr>
      <tr>
        <td>Weight:</td><td>${weight}g</td>
      </tr>
      <tr>
        <td>Quantity:</td><td>${quantity}</td>
      </tr>
      <tr>
        <td>RTS Code:</td><td>${rtsCode}</td>
      </tr>
    </table>
    <div id="qr-container"></div>
  `;

  generateQRCode(trackingNumber, "qr-container");
});

document.getElementById("download-png").addEventListener("click", () => {
  exportImage(document.getElementById("shipping-label"), "png");
});

document.getElementById("download-jpg").addEventListener("click", () => {
  exportImage(document.getElementById("shipping-label"), "jpg");
});