# Esquema: Inventario

Archivo: `inventario.json`

## Estructura
```json
{
  "personaje_id": "string (uuid)",
  
  "equipado": {
    "armadura": "string | null",
    "escudo": "string | null",
    "arma_principal": "string | null",
    "arma_secundaria": "string | null"
  },
  
  "objetos": [
    {
      "id": "string (uuid)",
      "nombre": "string",
      "cantidad": "number",
      "peso": "number",
      "categoria": "string (arma|armadura|escudo|consumible|herramienta|miscelanea)",
      "is_magical": "boolean",
      "descripcion": "string",
      "propiedades": {}
    }
  ],
  
  "capacidad_carga": {
    "peso_actual": "number",
    "peso_maximo": "number"
  }
}
```

## Notas

- `propiedades`: Objeto flexible para datos específicos del tipo de objeto
- Para armas: daño, tipo_daño, propiedades
- Para armaduras: CA_base, requisito_fuerza, desventaja_sigilo
- `is_magical`: Siempre presente, por defecto `false`
