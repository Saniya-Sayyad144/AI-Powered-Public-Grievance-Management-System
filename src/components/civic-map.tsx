import { useEffect, useRef } from "react";
import type { Map as LeafletMap, Marker } from "leaflet";
import "leaflet/dist/leaflet.css";
import { useCivic } from "./civic-context";

export type CivicMapPoint = { lat: number; lng: number; label?: string };

export function CivicMap({
  selectable = false,
  onSelect,
  points,
}: {
  selectable?: boolean;
  onSelect?: (value: string) => void;
  points?: CivicMapPoint[];
}) {
  const element = useRef<HTMLDivElement>(null);
  const { items } = useCivic();
  const visiblePoints =
    points ??
    items.flatMap((item) =>
      item.lat !== null && item.lng !== null
        ? [{ lat: item.lat, lng: item.lng, label: item.id }]
        : [],
    );
  const pointKey = visiblePoints
    .map((point) => `${point.lat},${point.lng},${point.label ?? ""}`)
    .join("|");
  const pointsRef = useRef(visiblePoints);
  pointsRef.current = visiblePoints;

  useEffect(() => {
    let map: LeafletMap | undefined;
    let mounted = true;
    void (async () => {
      const leaflet = await import("leaflet");
      if (!mounted || !element.current) return;
      const currentPoints = pointsRef.current;
      const firstPoint = currentPoints[0];
      const center: [number, number] = firstPoint
        ? [firstPoint.lat, firstPoint.lng]
        : [19.076, 72.878];
      map = leaflet
        .map(element.current, { zoomControl: true })
        .setView(center, firstPoint ? 13 : 12);
      leaflet
        .tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        })
        .addTo(map);
      currentPoints.forEach((point) =>
        leaflet
          .circleMarker([point.lat, point.lng], { radius: 8, color: "#087F8C", fillOpacity: 0.8 })
          .addTo(map!)
          .bindTooltip(point.label ?? "Reported civic issue"),
      );
      let selectedMarker: Marker | undefined;
      if (selectable)
        map.on("click", (event) => {
          selectedMarker?.remove();
          selectedMarker = leaflet.marker(event.latlng).addTo(map!);
          onSelect?.(`${event.latlng.lat.toFixed(4)}, ${event.latlng.lng.toFixed(4)}`);
        });
      window.setTimeout(() => map?.invalidateSize(), 100);
    })();
    return () => {
      mounted = false;
      map?.remove();
    };
  }, [onSelect, pointKey, selectable]);

  return <div ref={element} className="h-full min-h-72 w-full rounded-lg" />;
}
