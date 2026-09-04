const $ = id => document.getElementById(id);
function error(message = '') { $('error').textContent = message; $('error').hidden = !message; }
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : (result.detail || []).map(e => e.msg).join('; ') || 'Request failed.');
  return result;
}
function element(tag, text, className) {const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(className) node.className=className; return node;}
function value(v) {return typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(3) : String(v);}

function displayUnit(unit) {
  return ['count', 'dimensionless', 'e'].includes(unit) ? '' : unit;
}
function formulaNode(formula) {
  const span = element('span', undefined, 'formula');
  span.setAttribute('aria-label', formula);
  const charge = formula.match(/([+-])(\d*)$/);
  const body = charge ? formula.slice(0, charge.index) : formula;
  body.split(/(\d+)/).filter(Boolean).forEach(part => {
    span.append(element(/^\d+$/.test(part) ? 'sub' : 'span', part));
  });
  if (charge) span.append(element('sup', `${charge[2]}${charge[1]}`));
  return span;
}
function propertyCell(property, withUnit = false) {
  const cell = element('td');
  cell.append(property.name === 'Molecular formula' ? formulaNode(String(property.value)) : document.createTextNode(value(property.value)));
  const unit = displayUnit(property.unit);
  if (withUnit && unit) cell.append(document.createTextNode(` ${unit}`));
  return cell;
}
function descriptorTable(properties, compact = false) {
  const table = element('table'), head = element('tr');
  (compact ? ['Property', 'Computed value'] : ['Property', 'Computed value', 'Unit']).forEach(t => head.append(element('th', t)));
  table.append(head);
  properties.values.forEach(p => {
    const row = element('tr');
    row.append(element('td', p.name), propertyCell(p, compact));
    if (!compact) row.append(element('td', displayUnit(p.unit)));
    table.append(row);
  });
  return table;
}
